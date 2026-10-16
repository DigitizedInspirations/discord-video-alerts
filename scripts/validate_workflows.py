"""Structural YAML validation; not a substitute for GitHub runner execution."""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
for path in sorted((root / ".github/workflows").glob("*.yml*")):
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert "on" in data and "jobs" in data, path
    for job in data["jobs"].values():
        assert job.get("runs-on") == "ubuntu-latest", path
        assert "timeout-minutes" in job, path
    print("YAML valid:", path.name)
