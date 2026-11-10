"""Worker: takes queued executions from the database and runs them."""

import logging
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select, update

from . import config, curriculum, grader, runner
from .db import (
    Execution,
    LessonProgress,
    Project,
    create_schema,
    make_engine,
    make_session_factory,
    now,
)

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


def process(session_factory, lessons, execution_id: str, timeout_seconds: int) -> None:
    with session_factory() as session:
        execution = session.get(Execution, execution_id)
        project = session.get(Project, execution.project_id)
        lesson = lessons[project.lesson_id]
        files = dict(execution.files)
        operation = execution.operation

    assessment = None
    # The workspace is removed when this block ends, pass or fail.
    with tempfile.TemporaryDirectory(prefix="df-run-") as tmp:
        workspace = Path(tmp)
        try:
            runner.prepare_workspace(lesson, files, workspace)
            result = runner.HANDLERS[operation](workspace, timeout_seconds)
            if result.status != "timed_out":
                assessment = grader.grade(lesson, workspace)
        except Exception:  # one bad job must not stop the worker
            log.exception("execution %s failed in the worker", execution_id)
            result = runner.RunResult("failed", "Internal error. Run again.")

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


def run_once(session_factory, lessons, timeout_seconds: int) -> bool:
    execution_id = claim_next(session_factory)
    if execution_id is None:
        return False
    process(session_factory, lessons, execution_id, timeout_seconds)
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = make_engine()
    create_schema(engine)
    session_factory = make_session_factory(engine)
    lessons = curriculum.load_lessons()
    timeout_seconds = config.execution_timeout_seconds()
    log.info("worker started; lessons: %s", ", ".join(lessons))
    while True:
        fail_stale(session_factory, timeout_seconds)
        if not run_once(session_factory, lessons, timeout_seconds):
            time.sleep(1)


if __name__ == "__main__":
    main()
