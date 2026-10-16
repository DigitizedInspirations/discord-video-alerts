"""Narrow GitHub deployment/validation API, using existing Git credential helper.

Never prints or saves credential material. Never accesses a Discord secret. Read-only
operations plus dispatch of the two specifically allowlisted validation workflows.
"""
import argparse
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
    p.add_argument("operation", choices=["inspect", "dispatch", "runs", "run", "logs"])
    p.add_argument("--workflow", choices=["source-audit.yml", "validation.yml", "youtube-api-validation.yml", "durable-canary.yml"])
    p.add_argument("--expected-sha")
    p.add_argument("--phase", choices=["seed", "verify"])
    p.add_argument("--seed-run-id", type=int)
    p.add_argument("--run-id", type=int)
    args = p.parse_args()
    credential = token()
    def api(method, path, data=None):
        body = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(BASE+path, data=body, headers={"Authorization": "Bearer "+credential, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json", "User-Agent": "DiscordVideoAlerts-Validation"}, method=method)
        try:
            with open_private(req) as response:
                raw = response.read(30_000_000)
                return None if not raw else json.loads(raw)
        except urllib.error.HTTPError as exc:
            # Report HTTP status only; no tokens, raw request or response debug dumps.
            raise RuntimeError("GitHub API HTTP "+str(exc.code)) from None
        except (urllib.error.URLError, OSError, ValueError):
            raise RuntimeError("GitHub API network/response failure; sensitive details withheld") from None
    if args.operation == "inspect":
        repo = api("GET", "")
        print(json.dumps({k: repo.get(k) for k in ("full_name", "private", "default_branch", "permissions")}, indent=2))
        branch = api("GET", "/branches/main")
        print(json.dumps({"main_sha": branch["commit"]["sha"]}))
    elif args.operation == "dispatch":
        if not args.workflow:
            raise RuntimeError("Select an allowlisted validation workflow")
        if args.workflow in {"youtube-api-validation.yml", "durable-canary.yml"}:
            if not args.expected_sha or len(args.expected_sha) != 40:
                raise RuntimeError("API validation requires the reviewed main commit SHA")
            if api("GET", "/branches/main")["commit"]["sha"] != args.expected_sha:
                raise RuntimeError("Main changed; API validation dispatch refused")
        inputs = {}
        if args.workflow == "durable-canary.yml":
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
        api("POST", "/actions/workflows/"+args.workflow+"/dispatches", {"ref": "main", "inputs": inputs})
        print("Dispatched read-only workflow:", args.workflow)
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
        out = ROOT/"docs/cloud"
        out.mkdir(exist_ok=True)
        (out/(str(args.run_id)+"-result.json")).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    elif args.operation == "logs":
        if not args.run_id:
            raise RuntimeError("Run ID required")
        run = api("GET", "/actions/runs/"+str(args.run_id))
        if run.get("path") not in {".github/workflows/ci.yml", ".github/workflows/source-audit.yml", ".github/workflows/validation.yml", ".github/workflows/youtube-api-validation.yml", ".github/workflows/durable-canary.yml"}:
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
