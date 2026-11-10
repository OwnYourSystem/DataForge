"""Worker: takes queued executions from the database and runs them."""

import logging
import tempfile
import threading
import time
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select, update

from . import backends, config, curriculum, grader, runner
from .backends import Backend
from .db import (
    Execution,
    LessonProgress,
    Project,
    create_schema,
    make_engine,
    make_session_factory,
    now,
)
from .guard import GuardError

log = logging.getLogger("dataforge.worker")


def claim_next(session_factory) -> str | None:
    """Move one queued execution to `running`. Safe with more than one worker."""
    with session_factory() as session:
        candidate = session.scalar(
            select(Execution.id)
            .where(Execution.status == "queued")
            .order_by(Execution.created_at)
            .limit(1)
        )
        if candidate is None:
            return None
        claimed = session.execute(
            update(Execution)
            .where(Execution.id == candidate, Execution.status == "queued")
            .values(status="running", started_at=now())
        )
        session.commit()
        return candidate if claimed.rowcount == 1 else None


def fail_stale(session_factory, timeout_seconds: int) -> int:
    """Fail executions that a stopped worker left in `running`."""
    cutoff = now() - timedelta(seconds=timeout_seconds * 2 + 30)
    with session_factory() as session:
        result = session.execute(
            update(Execution)
            .where(Execution.status == "running", Execution.started_at < cutoff)
            .values(status="failed", finished_at=now(), logs="The worker stopped. Run again.")
        )
        session.commit()
        return result.rowcount


class BackendTimeout(RuntimeError):
    pass


def _bounded(function, seconds: int):
    """Run a backend call with a time limit. dbt has its own limit; these calls
    (grading, cleanup) use a network connection that can stop answering."""
    outcome: dict = {}

    def target():
        try:
            outcome["value"] = function()
        except BaseException as exc:  # passed to the caller below
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        raise BackendTimeout(f"no answer in {seconds} seconds")
    if "error" in outcome:
        raise outcome["error"]
    return outcome.get("value")


def process(
    session_factory, lessons, execution_id: str, timeout_seconds: int, backend: Backend
) -> None:
    with session_factory() as session:
        execution = session.get(Execution, execution_id)
        project = session.get(Project, execution.project_id)
        lesson = lessons[project.lesson_id]
        files = dict(execution.files)
        operation = execution.operation

    assessment = None
    call_timeout = config.backend_call_timeout_seconds()
    # The workspace is removed when this block ends, pass or fail.
    with tempfile.TemporaryDirectory(prefix="df-run-") as tmp:
        ctx = backend.new_context(execution_id, Path(tmp))
        try:
            runner.prepare_workspace(lesson, files, backend, ctx)
            result = runner.HANDLERS[operation](backend, ctx, timeout_seconds)
            if result.status != "timed_out":
                assessment = _bounded(lambda: grader.grade(lesson, backend, ctx), call_timeout)
        except GuardError as exc:
            result = runner.RunResult("failed", str(exc))
        except BackendTimeout:
            log.error("grading timed out for execution %s", execution_id)
            result = runner.RunResult(
                "failed", result.logs + "\n[The grader did not answer. Run again.]\n"
            )
        except Exception:  # one bad job must not stop the worker
            log.exception("execution %s failed in the worker", execution_id)
            result = runner.RunResult("failed", "Internal error. Run again.")
        finally:
            try:
                _bounded(lambda: backend.cleanup(ctx), call_timeout)
            except Exception:  # the sweep removes what stays
                log.exception("cleanup failed for execution %s", execution_id)

    with session_factory() as session:
        execution = session.get(Execution, execution_id)
        execution.status = result.status
        execution.logs = result.logs
        execution.assessment = assessment
        execution.finished_at = now()
        if assessment:
            progress = session.get(LessonProgress, execution.project_id) or LessonProgress(
                project_id=execution.project_id, best_score=0
            )
            progress.best_score = max(progress.best_score or 0, assessment["score"])
            if assessment["passed"] and progress.completed_at is None:
                progress.completed_at = now()
            session.add(progress)
        session.commit()


def run_once(session_factory, lessons, timeout_seconds: int, backend: Backend) -> bool:
    execution_id = claim_next(session_factory)
    if execution_id is None:
        return False
    process(session_factory, lessons, execution_id, timeout_seconds, backend)
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = make_engine()
    create_schema(engine)
    session_factory = make_session_factory(engine)
    lessons = curriculum.load_lessons()
    timeout_seconds = config.execution_timeout_seconds()
    backend = backends.load()
    log.info("worker started; backend: %s; lessons: %s", backend.name, ", ".join(lessons))
    next_sweep = 0.0
    while True:
        fail_stale(session_factory, timeout_seconds)
        if time.monotonic() >= next_sweep:
            next_sweep = time.monotonic() + config.sweep_interval_seconds()
            try:
                # Older than every run that can still be active.
                removed = _bounded(
                    lambda: backend.sweep(max_age_minutes=timeout_seconds * 2 // 60 + 10),
                    config.backend_call_timeout_seconds(),
                )
                if removed:
                    log.info("sweep removed %s orphan schemas", removed)
            except Exception:
                log.exception("sweep failed")
        if not run_once(session_factory, lessons, timeout_seconds, backend):
            time.sleep(1)


if __name__ == "__main__":
    main()
