"""Run the repository checks before opening a pull request with GitHub CLI."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    subprocess.run(
        (sys.executable, "-m", "pytest"),
        cwd=repository,
        check=True,
    )
    subprocess.run(
        (sys.executable, "-m", "compileall", "-q", "src/ml_training_loop"),
        cwd=repository,
        check=True,
    )
    gh = shutil.which("gh")
    if gh is None:
        raise SystemExit("GitHub CLI is unavailable; install and authenticate gh")
    return subprocess.run(
        (gh, "pr", "create", *sys.argv[1:]),
        cwd=repository,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
