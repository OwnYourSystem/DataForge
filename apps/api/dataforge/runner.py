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

import yaml

from .backends import Backend, RunContext
from .curriculum import Lesson
from .guard import check_learner_sql

MAX_LOG_CHARS = 20_000


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


def prepare_workspace(
    lesson: Lesson, files: dict[str, str], backend: Backend, ctx: RunContext, guard: bool = True
) -> None:
    """Copy the trusted project, add the approved learner files, write the profile."""
    workspace = ctx.workspace
    shutil.copytree(lesson.project_dir, workspace, dirs_exist_ok=True)
    for path in lesson.editable_files:
        if guard:
            # The API checks on save. The worker checks again before a run.
            check_learner_sql(files[path], backend.dialect)
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(files[path])
    project_path = workspace / "dbt_project.yml"
    project = yaml.safe_load(project_path.read_text())
    # Each query carries the execution id, so that cost and duration in the
    # engine's query history can be joined to one run.
    project["query-comment"] = {
        "comment": f"dataforge_execution={ctx.execution_id}",
        "append": True,
    }
    project_path.write_text(yaml.safe_dump(project, sort_keys=False))
    _write_profile(backend, ctx, backend.build_target)


def _write_profile(backend: Backend, ctx: RunContext, target: str) -> None:
    """Write a profile with one target only: the target of the next step.

    A step then cannot use the credential of a different step.
    """
    project = yaml.safe_load((ctx.workspace / "dbt_project.yml").read_text())
    profile = {
        project["profile"]: {"target": target, "outputs": {target: backend.profile(ctx)[target]}}
    }
    (ctx.workspace / "profiles.yml").write_text(yaml.safe_dump(profile, sort_keys=False))


def _sanitize(text: str, workspace: Path, secrets: list[str]) -> str:
    text = text.replace(str(workspace), "/workspace")
    for secret in secrets:
        text = text.replace(secret, "[redacted]")
    if len(text) > MAX_LOG_CHARS:
        text = text[:MAX_LOG_CHARS] + "\n[log truncated]\n"
    return text


def dbt_build(backend: Backend, ctx: RunContext, timeout_seconds: int) -> RunResult:
    """Load the seed (trusted step), then build and test the learner model."""
    dbt = _dbt_executable()
    workspace = ctx.workspace
    # A minimal environment. The worker's own variables do not go to dbt.
    base_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(workspace),
        "DO_NOT_TRACK": "1",
    }
    for name in ("HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy", "SSL_CERT_FILE",
                 "REQUESTS_CA_BUNDLE"):  # fmt: skip
        if name in os.environ:
            base_env[name] = os.environ[name]
    common = ["--profiles-dir", ".", "--no-use-colors", "--no-version-check"]
    # (target, arguments). The seed step is trusted. The build step runs learner SQL.
    steps = [
        (backend.seed_target, [dbt, "seed", "--target", backend.seed_target, *common]),
        (backend.build_target, [dbt, "build", "--exclude-resource-type", "seed", "--target",
                                backend.build_target, *common]),
    ]  # fmt: skip
    secrets = backend.secrets()
    deadline = time.monotonic() + timeout_seconds
    logs: list[str] = []

    def result(status: str) -> RunResult:
        return RunResult(status, _sanitize("".join(logs), workspace, secrets))

    for target, argv in steps:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logs.append("\n[stopped: time limit]\n")
            return result("timed_out")
        logs.append(f"$ dbt {argv[1]}\n")
        _write_profile(backend, ctx, target)
        env = {**base_env, **backend.env(ctx, target)}
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
            output = exc.stdout or ""
            logs.append(output.decode(errors="replace") if isinstance(output, bytes) else output)
            logs.append("\n[stopped: time limit]\n")
            return result("timed_out")
        logs.append(done.stdout)
        if done.returncode != 0:
            return result("failed")
    return result("succeeded")


HANDLERS = {"dbt_build": dbt_build}
