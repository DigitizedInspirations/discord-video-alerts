"""Extract only public validation reports from previously downloaded workflow logs."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for argument in sys.argv[1:]:
    run_id = str(int(argument))
    result_path = ROOT / "docs/cloud" / (run_id + "-result.json")
    run = json.loads(result_path.read_text(encoding="utf-8"))["run"]
    evidence = {"run": run, "reports": {}, "unittest_counts": [], "runner_names": [], "machine_names": []}
    for path in sorted((ROOT / ".validation" / run_id).rglob("*.txt")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            for label, key in (("Runner name:", "runner_names"), ("Machine name:", "machine_names")):
                if label in line:
                    value = line.split(label, 1)[1].strip()[:160]
                    if value not in evidence[key]:
                        evidence[key].append(value)
            for marker in ("DVA_REPORT ", "DVA_YOUTUBE_DIAGNOSTIC ", "DVA_YOUTUBE_RUNTIME_DIAGNOSTIC "):
                if marker in line:
                    try:
                        report = json.loads(line.split(marker, 1)[1])
                    except ValueError:
                        continue
                    evidence["reports"][marker.strip()] = report
            match = re.search(r"\bRan (\d+) tests in ", line)
            if match:
                count = int(match[1])
                if count not in evidence["unittest_counts"]:
                    evidence["unittest_counts"].append(count)
    target = result_path.with_name(run_id + "-evidence.json")
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(run_id, run["conclusion"], "reports:", list(evidence["reports"]),
          "unittest counts:", evidence["unittest_counts"])
