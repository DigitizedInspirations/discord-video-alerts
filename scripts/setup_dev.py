"""Create a project-local development environment and a reproducible dependency lock."""
import subprocess
import sys
import venv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = root / ".venv"
venv.EnvBuilder(with_pip=True).create(env)
python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--only-binary=:all:", "-r", str(root / "requirements.in")], check=True, cwd=root)
result = subprocess.run([str(python), "-m", "pip", "freeze"], capture_output=True, text=True, check=True, cwd=root)
(root / "requirements.lock").write_text(result.stdout, encoding="utf-8")
print("Environment ready; dependencies pinned in requirements.lock")
