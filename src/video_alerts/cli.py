import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from .adapters import adapters
from .config import load_config
from .discord import DiscordClient
from .engine import Engine
from .model import AlertError
from .state import GitHubStore, LocalStore, MemoryStore, decode, encode, merge_restore

@contextmanager
def local_lock(root):
    directory = root / "state"
    directory.mkdir(exist_ok=True)
    path = directory / "operator.lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise AlertError("Another local run or stale operator.lock exists; inspect the process before removing it") from None
    try:
        with os.fdopen(fd, "w") as file:
            file.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)

def summary(state):
    rows = ["## Κατάσταση Discord Video Alerts", "", "| Πηγή | Κατάσταση | Αποτυχίες | Τελευταίος επιτυχής έλεγχος |", "|---|---|---|---|"]
    for sid, source in state["sources"].items():
        rows.append(f"| {sid} | {source['status']} | {source['consecutive_failures']} | {source.get('last_success') or '—'} |")
        if source.get("error"):
            rows.append(f"\nΠρόβλημα {sid}: {source['error']}\n")
    counts = {}
    for record in state["records"].values():
        counts[record["status"]] = counts.get(record["status"], 0) + 1
    rows += ["", "Καταγραφές: " + json.dumps(counts, ensure_ascii=False), "", "HEALTHY σημαίνει επιτυχή ανάγνωση πηγής, όχι εγγύηση πλήρους κάλυψης ή επιτυχούς Discord playback."]
    text = "\n".join(rows) + "\n"
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if destination:
        with open(destination, "a", encoding="utf-8") as file:
            file.write(text)
    else:
        print(text)

def parser():
    p = argparse.ArgumentParser(description="Discord Video Alerts — conservative notification operations")
    p.add_argument("operation", choices=["validate", "initialize", "monitor", "dryrun", "manual", "test", "show", "edit", "delete", "resolve", "restore"])
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--github", action="store_true")
    p.add_argument("--source", default=os.getenv("INPUT_SOURCE", "youtube_dayz"))
    p.add_argument("--url", default=os.getenv("INPUT_VIDEO_URL", ""))
    p.add_argument("--post-id", default=os.getenv("INPUT_POST_ID", ""))
    p.add_argument("--message-id", default=os.getenv("INPUT_MESSAGE_ID", ""))
    p.add_argument("--confirmation", default=os.getenv("INPUT_CONFIRMATION", ""))
    p.add_argument("--restore-ref", default=os.getenv("INPUT_RESTORE_REF", ""))
    p.add_argument("--live", action="store_true", default=os.getenv("INPUT_LIVE") == "true")
    p.add_argument("--repost", action="store_true", default=os.getenv("INPUT_REPOST") == "true")
    p.add_argument("--url-only", action="store_true", default=os.getenv("INPUT_USE_TEMPLATE") == "false")
    return p

def execute(args):
    root = args.root.resolve()
    cfg = load_config(root)
    if args.operation == "validate":
        print("Ρυθμίσεις και τέσσερα UTF-8 πρότυπα: έγκυρα")
        return
    store = GitHubStore(os.getenv("GITHUB_REPOSITORY", ""), os.getenv("GITHUB_TOKEN", "")) if args.github else LocalStore(root / "state/state.json")
    if args.operation == "initialize":
        if args.confirmation != "INITIALIZE":
            raise AlertError("Initialization requires INITIALIZE confirmation")
        store.initialize()
        print("Αρχικοποίηση χωρίς ανακοίνωση ιστορικού περιεχομένου")
        return
    if args.operation == "restore":
        if args.confirmation != "RESTORE":
            raise AlertError("Restore requires RESTORE confirmation")
        if args.github:
            store.restore(args.restore_ref, args.confirmation)
        else:
            backup_path = root / "state" / args.restore_ref
            if backup_path.resolve().parent != (root / "state").resolve() or not backup_path.is_file():
                raise AlertError("Restore file must be inside state/ with a simple filename")
            backup = decode(backup_path.read_bytes())
            try:
                current = store.load()
            except AlertError:
                # With missing/corrupt current state, quarantine restored queue and force new baselines.
                for source in backup["sources"].values():
                    source.update(active=False, baseline_needed=True)
                for record in backup["records"].values():
                    if record["status"] in {"sending", "queued", "waiting_metadata"}:
                        record["status"] = "uncertain"
                store.restore(encode(backup), "RESTORE")
            else:
                store.restore(encode(merge_restore(current, backup)), "RESTORE")
        print("Ανάκτηση επικυρωμένου checkpoint. Ελέγξτε uncertain εγγραφές πριν από αποστολές.")
        return
    readonly = args.operation == "dryrun" or (args.operation in {"manual", "test"} and not args.live)
    if readonly:
        try:
            state = store.load()
        except AlertError:
            # Never mask corrupt/missing durable state. Use initialize explicitly.
            raise
        store = MemoryStore(state)
    client = None
    if args.live or args.operation in {"edit", "delete", "resolve"}:
        required = args.operation.upper() if args.operation in {"edit", "delete", "resolve"} else "REPOST" if args.repost else "SEND"
        if args.confirmation != required:
            raise AlertError(f"Live operation requires {required} confirmation")
        client = DiscordClient(os.getenv("DISCORD_WEBHOOK_URL", ""), cfg["retry"])
    engine = Engine(root, cfg, store, adapters(cfg), client)
    try:
        if args.operation in {"monitor", "dryrun"}:
            engine.run(deliver=args.live and args.operation != "dryrun")
        elif args.operation in {"manual", "test"}:
            url = args.url or ("https://www.youtube.com/shorts/DVUoG6SSUUI" if args.operation == "test" else "")
            result = engine.manual(args.source, url, args.live, args.repost, args.confirmation, not args.url_only, args.operation == "test")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            result = engine.manage(args.source, args.post_id, args.operation, args.confirmation, args.message_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        summary(engine.state)

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args()
    try:
        if args.github or args.operation == "validate":
            execute(args)
        else:
            with local_lock(args.root.resolve()):
                execute(args)
    except AlertError as exc:
        print("Σφάλμα: " + str(exc), file=sys.stderr)
        return 1
    except Exception:
        # Prevent unhandled urllib/SDK exception tracebacks from leaking credentials.
        print("Σφάλμα εφαρμογής· τα ευαίσθητα στοιχεία αποκρύφθηκαν. Ελέγξτε το handoff και τις δοκιμές.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
