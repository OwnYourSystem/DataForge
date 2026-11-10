"""Trusted operation handlers. They run dbt with fixed argument lists.

The learner sends an operation id only. No learner text goes into a command.
"""

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .curriculum import Lesson

MAX_LOG_CHARS = 20_000
DUCKDB_FILE = "lab.duckdb"


@dataclass
class RunResult:
    status: str  # succeeded, failed, timed_out
    logs: str


def _dbt_executable() -> str:
    beside_python = Path(sys.executable).parent / "dbt"
    if beside_python.exists():
        return str(beside_python)
    found = shutil.which("dbt")
    if not found:
        raise RuntimeError("dbt is not installed. Install the `worker` dependency group.")
    return found


def prepare_workspace(lesson: Lesson, files: dict[str, str], workspace: Path) -> None:
    """Copy the trusted project, then add only the approved learner files."""
    shutil.copytree(lesson.project_dir, workspace, dirs_exist_ok=True)
    for path in lesson.editable_files:
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(files[path])


def _sanitize(text: str, workspace: Path) -> str:
    text = text.replace(str(workspace), "/workspace")
    if len(text) > MAX_LOG_CHARS:
        text = text[:MAX_LOG_CHARS] + "\n[log truncated]\n"
    return text


def dbt_build(workspace: Path, timeout_seconds: int) -> RunResult:
    """Load the seed (trusted target), then build and test (locked target)."""
    dbt = _dbt_executable()
    # A minimal environment. The worker's own variables do not go to dbt.
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(workspace),
        "DF_DUCKDB_PATH": str(workspace / DUCKDB_FILE),
        "DO_NOT_TRACK": "1",
    }
    common = ["--profiles-dir", ".", "--no-use-colors", "--no-version-check"]
    steps = [
        [dbt, "seed", "--target", "seed", *common],
        [dbt, "build", "--exclude-resource-type", "seed", "--target", "learner", *common],
    ]
    deadline = time.monotonic() + timeout_seconds
    logs: list[str] = []
    for argv in steps:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return RunResult("timed_out", _sanitize("".join(logs), workspace))
        logs.append(f"$ dbt {argv[1]}\n")
        try:
            done = subprocess.run(
                argv,
                cwd=workspace,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=remaining,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            logs.append(
                (exc.stdout or b"").decode(errors="replace")
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            )
            logs.append("\n[stopped: time limit]\n")
            return RunResult("timed_out", _sanitize("".join(logs), workspace))
        logs.append(done.stdout)
        if done.returncode != 0:
            return RunResult("failed", _sanitize("".join(logs), workspace))
    return RunResult("succeeded", _sanitize("".join(logs), workspace))


HANDLERS = {"dbt_build": dbt_build}
