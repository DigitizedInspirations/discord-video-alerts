"""Narrow GitHub deployment/validation API, using existing Git credential helper.

Never prints or saves credential material. Never accesses a Discord secret. Read-only
operations plus dispatch of specifically allowlisted validation workflows.
"""
import argparse
import base64
import io
import json
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO = "DigitizedInspirations/discord-video-alerts"
BASE = "https://api.github.com/repos/"+REPO

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def open_private(req):
    return urllib.request.build_opener(NoRedirect).open(req, timeout=30)

def token():
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\npath="+REPO+".git\n\n", text=True, capture_output=True, cwd=ROOT, timeout=90)
    if result.returncode:
        raise RuntimeError("Existing Git credential helper could not authenticate; no credential values displayed")
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    value = fields.get("password")
    if not value:
        raise RuntimeError("No existing GitHub credential available")
    return value

def main():
    p = argparse.ArgumentParser()
    p.add_argument("operation", choices=["inspect", "production-preflight", "baseline-preflight", "dispatch", "runs", "run", "logs"])
    p.add_argument("--workflow", choices=["source-audit.yml", "validation.yml", "youtube-api-validation.yml", "durable-canary.yml", "initialize-state.yml", "baseline-state.yml"])
    p.add_argument("--confirmation")
    p.add_argument("--authorization-id")
    p.add_argument("--expected-sha")
    p.add_argument("--phase", choices=["seed", "verify"])
    p.add_argument("--seed-run-id", type=int)
    p.add_argument("--run-id", type=int)
    args = p.parse_args()
    credential = token()
    def api(method, path, data=None, allow_missing=False):
        body = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(BASE+path, data=body, headers={"Authorization": "Bearer "+credential, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json", "User-Agent": "DiscordVideoAlerts-Validation"}, method=method)
        try:
            with open_private(req) as response:
                raw = response.read(30_000_000)
                return None if not raw else json.loads(raw)
        except urllib.error.HTTPError as exc:
            if allow_missing and method == "GET" and exc.code == 404:
                return None
            # Report HTTP status only; no tokens, raw request or response debug dumps.
            raise RuntimeError("GitHub API HTTP "+str(exc.code)) from None
        except (urllib.error.URLError, OSError, ValueError):
            raise RuntimeError("GitHub API network/response failure; sensitive details withheld") from None
    def production_preflight(expected_sha=None):
        repo = api("GET", "")
        main_sha = api("GET", "/git/ref/heads/main")["object"]["sha"]
        if repo.get("full_name") != REPO or repo.get("default_branch") != "main":
            raise RuntimeError("Production preflight repository/default branch mismatch")
        if expected_sha is not None and main_sha != expected_sha:
            raise RuntimeError("Reviewed main changed; production dispatch refused")
        if api("GET", "/git/ref/heads/notification-state", allow_missing=True) is not None:
            raise RuntimeError("Production branch already exists; initialization refused")
        if api("GET", "/contents/state.json?ref=notification-state", allow_missing=True) is not None:
            raise RuntimeError("Production state already exists; initialization refused")
        return {"repository": REPO, "main_sha": main_sha, "production_branch_absent": True, "production_file_absent": True}

    def baseline_preflight(expected_sha):
        sys.path.insert(0, str(ROOT/"src"))
        from video_alerts.production_baseline import (REPOSITORY, INITIAL_COMMIT, INITIAL_STATE,
            INITIAL_HASH, INITIAL_BLOB, HISTORY, checksum, settings)
        from video_alerts.state import decode
        settings(ROOT)
        repo = api("GET", "")
        if repo.get("full_name") != REPOSITORY or repo.get("default_branch") != "main" or api("GET", "/git/ref/heads/main")["object"]["sha"] != expected_sha:
            raise RuntimeError("Baseline trusted repository/reviewed main mismatch")
        if api("GET", "/git/ref/heads/notification-state")["object"]["sha"] != INITIAL_COMMIT:
            raise RuntimeError("Baseline requires unchanged initial production commit")
        value = api("GET", "/contents/state.json?ref=notification-state")
        state = decode(base64.b64decode(value["content"], validate=False))
        if state != INITIAL_STATE or checksum(state) != INITIAL_HASH or value["sha"] != INITIAL_BLOB:
            raise RuntimeError("Baseline initial state identity/checksum/blob mismatch")
        history = api("GET", HISTORY)
        if history.get("total_count") != 0 or history.get("workflow_runs") != []:
            raise RuntimeError("Single baseline attempt already consumed; no additional dispatch")
        return {"repository": REPOSITORY, "main_sha": expected_sha, "production_commit": INITIAL_COMMIT,
                "initial_state_sha256": INITIAL_HASH, "initial_blob": INITIAL_BLOB,
                "baseline_run_count": 0, "production_state_writes": 0}

    if args.operation == "baseline-preflight":
        print(json.dumps(baseline_preflight(args.expected_sha), indent=2))
    elif args.operation == "production-preflight":
        print(json.dumps(production_preflight(args.expected_sha), indent=2))
    elif args.operation == "inspect":
        repo = api("GET", "")
        print(json.dumps({k: repo.get(k) for k in ("full_name", "private", "default_branch", "permissions")}, indent=2))
        branch = api("GET", "/branches/main")
        print(json.dumps({"main_sha": branch["commit"]["sha"]}))
    elif args.operation == "dispatch":
        if not args.workflow:
            raise RuntimeError("Select an allowlisted validation workflow")
        if args.workflow in {"youtube-api-validation.yml", "durable-canary.yml", "initialize-state.yml", "baseline-state.yml"}:
            if not args.expected_sha or len(args.expected_sha) != 40:
                raise RuntimeError("Controlled validation requires the reviewed main commit SHA")
            if api("GET", "/branches/main")["commit"]["sha"] != args.expected_sha:
                raise RuntimeError("Main changed; controlled validation dispatch refused")
        inputs = {}
        if args.workflow == "baseline-state.yml":
            sys.path.insert(0, str(ROOT/"src"))
            from video_alerts.production_baseline import AUTHORIZATION, CONFIRMATION, BRANCH
            if args.confirmation != CONFIRMATION or args.authorization_id != AUTHORIZATION:
                raise RuntimeError("Exact single-attempt baseline authorization and confirmation required")
            baseline_preflight(args.expected_sha)
            inputs = {"repository": REPO, "branch": BRANCH, "authorization": AUTHORIZATION,
                      "confirmation": CONFIRMATION, "expected_sha": args.expected_sha}
        elif args.workflow == "durable-canary.yml":
            sys.path.insert(0, str(ROOT/"src"))
            from video_alerts.canary import APPROVED_BRANCH
            runs = api("GET", "/actions/workflows/durable-canary.yml/runs?event=workflow_dispatch&per_page=100")["workflow_runs"]
            if args.phase == "seed":
                if runs:
                    raise RuntimeError("Canary seed already dispatched; no automatic repeat permitted")
            elif args.phase == "verify":
                if len(runs) != 1 or not args.seed_run_id or runs[0]["id"] != args.seed_run_id:
                    raise RuntimeError("Canary verify requires exactly one prior seed run")
                seed = api("GET", "/actions/runs/"+str(args.seed_run_id))
                if seed.get("conclusion") != "success" or seed.get("head_sha") != args.expected_sha or seed.get("head_branch") != "main" or seed.get("run_attempt") != 1:
                    raise RuntimeError("Canary seed not completed successfully on reviewed main")
            else:
                raise RuntimeError("Canary phase is required")
            inputs = {"phase": args.phase, "branch": APPROVED_BRANCH, "expected_sha": args.expected_sha,
                      "seed_run_id": str(args.seed_run_id) if args.seed_run_id else ""}
        elif args.workflow == "initialize-state.yml":
            sys.path.insert(0, str(ROOT/"src"))
            from video_alerts.production_init import CONFIRMATION, OPERATION, BRANCH, guard_local_settings
            from video_alerts.initialization_authorization import authorize_dispatch, PREVIOUS_RUN
            from video_alerts.model import AlertError
            if args.confirmation != CONFIRMATION:
                raise RuntimeError("Exact one-time empty production initialization confirmation required")
            try:
                guard_local_settings(ROOT)
            except AlertError as exc:
                raise RuntimeError(str(exc)) from None
            production_preflight(args.expected_sha)
            runs = api("GET", "/actions/workflows/initialize-state.yml/runs?event=workflow_dispatch&per_page=100")["workflow_runs"]
            previous = api("GET", "/actions/runs/" + str(PREVIOUS_RUN))
            try:
                authorize_dispatch(ROOT, args.authorization_id, runs, previous)
            except AlertError as exc:
                raise RuntimeError(str(exc)) from None
            inputs = {"repository": REPO, "branch": BRANCH, "operation": OPERATION,
                      "confirmation": CONFIRMATION, "expected_sha": args.expected_sha}
        api("POST", "/actions/workflows/"+args.workflow+"/dispatches", {"ref": "main", "inputs": inputs})
        label = "Dispatched controlled state workflow:" if args.workflow in {"durable-canary.yml", "initialize-state.yml", "baseline-state.yml"} else "Dispatched read-only workflow:"
        print(label, args.workflow)
    elif args.operation == "runs":
        value = api("GET", "/actions/runs?per_page=12")
        for run in value["workflow_runs"]:
            print(json.dumps({k: run.get(k) for k in ("id", "name", "head_sha", "event", "status", "conclusion", "html_url", "created_at")}))
    elif args.operation == "run":
        if not args.run_id:
            raise RuntimeError("Run ID required")
        run = api("GET", "/actions/runs/"+str(args.run_id))
        jobs = api("GET", "/actions/runs/"+str(args.run_id)+"/jobs")
        result = {"run": {k: run.get(k) for k in ("id", "name", "head_sha", "status", "conclusion", "html_url")}, "jobs": [{"id": j["id"], "name": j["name"], "status": j["status"], "conclusion": j["conclusion"], "steps": [{"name": s["name"], "conclusion": s["conclusion"]} for s in j.get("steps", [])]} for j in jobs["jobs"]]}
        for entry, job in zip(result["jobs"], jobs["jobs"]):
            entry.update(runner_id=job.get("runner_id"), runner_name=job.get("runner_name"), labels=job.get("labels", []))
        out = ROOT/"docs/cloud"
        out.mkdir(exist_ok=True)
        (out/(str(args.run_id)+"-result.json")).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    elif args.operation == "logs":
        if not args.run_id:
            raise RuntimeError("Run ID required")
        run = api("GET", "/actions/runs/"+str(args.run_id))
        if run.get("path") not in {".github/workflows/ci.yml", ".github/workflows/source-audit.yml", ".github/workflows/validation.yml", ".github/workflows/youtube-api-validation.yml", ".github/workflows/durable-canary.yml", ".github/workflows/initialize-state.yml", ".github/workflows/baseline-state.yml"}:
            raise RuntimeError("Only approved validation workflow logs may be fetched")
        req = urllib.request.Request(BASE+"/actions/runs/"+str(args.run_id)+"/logs", headers={"Authorization": "Bearer "+credential, "Accept": "application/vnd.github+json", "User-Agent": "DiscordVideoAlerts-Validation"})
        try:
            with open_private(req) as response:
                raw = response.read(30_000_000)
        except urllib.error.HTTPError as exc:
            if exc.code != 302:
                raise RuntimeError("Validation log download HTTP "+str(exc.code)) from None
            location = exc.headers.get("Location", "")
            target_url = urlsplit(location)
            host = target_url.hostname or ""
            if target_url.scheme != "https" or target_url.username or target_url.password or not (host.endswith(".blob.core.windows.net") or host.endswith(".actions.githubusercontent.com")):
                raise RuntimeError("Unrecognized validation log download host; redirect refused")
            # Authentication is deliberately absent on the signed storage request.
            clean = urllib.request.Request(location, headers={"User-Agent": "DiscordVideoAlerts-Validation"})
            with open_private(clean) as response:
                raw = response.read(30_000_000)
        except (urllib.error.URLError, OSError):
            raise RuntimeError("Cannot retrieve validation logs; sensitive details withheld") from None
        out = ROOT/".validation"/str(args.run_id)
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            count = 0
            for name in archive.namelist():
                target = (out/name).resolve()
                if not target.is_relative_to(out.resolve()) or not name.endswith(".txt") or archive.getinfo(name).file_size > 10_000_000:
                    continue
                data = archive.read(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                count += 1
                # Show only bounded, relevant result/error lines, never full env/debug logs.
                text = data.decode("utf-8", "replace")
                for line in text.splitlines():
                    if any(marker in line for marker in ("DVA_REPORT", "DVA_YOUTUBE_DIAGNOSTIC", "DVA_YOUTUBE_RUNTIME_DIAGNOSTIC", "Ran ", "FAILED (", "##[error]", "exit code", "Checking youtube", "Checking tiktok", '"discovery":', '"metadata":')):
                        print(line[:2200])
        print("Validation logs saved locally (ignored):", count)

if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        main()
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            print(str(exc), file=sys.stderr)
        else:
            print("GitHub validation control failed; credential details withheld", file=sys.stderr)
        raise SystemExit(1)
