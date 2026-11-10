"""HTTP API (control plane). It does not run learner code."""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import backends, config, curriculum
from .auth import identity_subject
from .db import (
    Execution,
    LessonProgress,
    Project,
    ProjectFile,
    User,
    create_schema,
    make_engine,
    make_session_factory,
    now,
)
from .guard import GuardError, check_learner_sql


class CreateProject(BaseModel):
    lesson_id: str


class SaveFile(BaseModel):
    content: str


class CreateExecution(BaseModel):
    operation_id: str


def create_app(engine=None, lessons=None, dialect: str | None = None) -> FastAPI:
    engine = engine or make_engine()
    create_schema(engine)
    session_factory = make_session_factory(engine)
    lessons = lessons if lessons is not None else curriculum.load_lessons()
    # The API needs the SQL dialect for the guard. It does not load the backend.
    dialect = backends.dialect(dialect)

    app = FastAPI(title="DataForge API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.session_factory = session_factory

    def db():
        with session_factory() as session:
            yield session

    def current_user(
        subject: str = Depends(identity_subject), session: Session = Depends(db)
    ) -> User:
        user = session.scalar(select(User).where(User.identity_subject == subject))
        if user is None:
            user = User(identity_subject=subject)
            session.add(user)
            try:
                session.commit()
            except IntegrityError:  # a parallel request created the user
                session.rollback()
                user = session.scalar(select(User).where(User.identity_subject == subject))
        return user

    def owned_project(project_id: str, user: User, session: Session) -> Project:
        project = session.get(Project, project_id)
        # 404 for a project of a different user, so that ids do not leak.
        if project is None or project.user_id != user.id:
            raise HTTPException(404, "Project not found.")
        return project

    def execution_view(execution: Execution) -> dict:
        duration = None
        if execution.started_at and execution.finished_at:
            duration = round((execution.finished_at - execution.started_at).total_seconds(), 2)
        return {
            "id": execution.id,
            "project_id": execution.project_id,
            "operation_id": execution.operation,
            "status": execution.status,
            "logs": execution.logs,
            "assessment": execution.assessment,
            "compute_seconds": duration,
            "created_at": execution.created_at,
        }

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/v1/me")
    def me(user: User = Depends(current_user)):
        return {"id": user.id, "identity_subject": user.identity_subject}

    @app.get("/v1/lessons")
    def list_lessons(user: User = Depends(current_user)):
        return [{"id": x.id, "version": x.version, "title": x.title} for x in lessons.values()]

    @app.get("/v1/lessons/{lesson_id}")
    def get_lesson(lesson_id: str, user: User = Depends(current_user)):
        lesson = lessons.get(lesson_id)
        if lesson is None:
            raise HTTPException(404, "Lesson not found.")
        return {
            "id": lesson.id,
            "version": lesson.version,
            "title": lesson.title,
            "objectives": lesson.manifest.get("objectives", []),
            "editable_files": lesson.editable_files,
            "operations": lesson.manifest["operations"],
            "instructions": lesson.instructions(),
        }

    @app.post("/v1/projects")
    def create_project(
        body: CreateProject, user: User = Depends(current_user), session: Session = Depends(db)
    ):
        """One project for each user and lesson. A second call returns the same project."""
        lesson = lessons.get(body.lesson_id)
        if lesson is None:
            raise HTTPException(404, "Lesson not found.")
        query = select(Project).where(Project.user_id == user.id, Project.lesson_id == lesson.id)
        project = session.scalar(query)
        if project is None:
            project = Project(user_id=user.id, lesson_id=lesson.id, lesson_version=lesson.version)
            session.add(project)
            try:
                session.flush()
                for path, content in lesson.starter_files().items():
                    session.add(ProjectFile(project_id=project.id, path=path, content=content))
                session.commit()
            except IntegrityError:
                session.rollback()
                project = session.scalar(query)
        return {"id": project.id, "lesson_id": project.lesson_id}

    @app.get("/v1/projects/{project_id}")
    def get_project(
        project_id: str, user: User = Depends(current_user), session: Session = Depends(db)
    ):
        project = owned_project(project_id, user, session)
        progress = session.get(LessonProgress, project.id)
        return {
            "id": project.id,
            "lesson_id": project.lesson_id,
            "best_score": progress.best_score if progress else 0,
            "completed_at": progress.completed_at if progress else None,
        }

    @app.get("/v1/projects/{project_id}/files")
    def list_files(
        project_id: str, user: User = Depends(current_user), session: Session = Depends(db)
    ):
        project = owned_project(project_id, user, session)
        files = session.scalars(
            select(ProjectFile)
            .where(ProjectFile.project_id == project.id)
            .order_by(ProjectFile.path)
        )
        return [{"path": f.path, "content": f.content, "updated_at": f.updated_at} for f in files]

    @app.put("/v1/projects/{project_id}/files/{path:path}")
    def save_file(
        project_id: str,
        path: str,
        body: SaveFile,
        user: User = Depends(current_user),
        session: Session = Depends(db),
    ):
        project = owned_project(project_id, user, session)
        # An exact-match allowlist. This also stops path traversal.
        if path not in lessons[project.lesson_id].editable_files:
            raise HTTPException(403, "You cannot change this file.")
        try:
            check_learner_sql(body.content, dialect)
        except GuardError as exc:
            raise HTTPException(422, str(exc)) from exc
        file = session.get(ProjectFile, (project.id, path))
        file.content = body.content
        file.updated_at = now()
        session.commit()
        return {"path": path, "updated_at": file.updated_at}

    @app.post("/v1/projects/{project_id}/executions", status_code=202)
    def create_execution(
        project_id: str,
        body: CreateExecution,
        user: User = Depends(current_user),
        session: Session = Depends(db),
    ):
        project = owned_project(project_id, user, session)
        lesson = lessons[project.lesson_id]
        if body.operation_id not in lesson.operation_ids:
            raise HTTPException(422, "This operation is not approved for the lesson.")
        # Quota: one active execution for each user.
        active = session.scalar(
            select(Execution.id).where(
                Execution.user_id == user.id, Execution.status.in_(["queued", "running"])
            )
        )
        if active:
            raise HTTPException(409, "An execution is in progress. Wait until it is complete.")
        files = {
            f.path: f.content
            for f in session.scalars(
                select(ProjectFile).where(ProjectFile.project_id == project.id)
            )
        }
        execution = Execution(
            project_id=project.id, user_id=user.id, operation=body.operation_id, files=files
        )
        session.add(execution)
        session.commit()
        return {
            "id": execution.id,
            "status": execution.status,
            "status_url": f"/v1/executions/{execution.id}",
        }

    @app.get("/v1/executions/{execution_id}")
    def get_execution(
        execution_id: str, user: User = Depends(current_user), session: Session = Depends(db)
    ):
        execution = session.get(Execution, execution_id)
        if execution is None or execution.user_id != user.id:
            raise HTTPException(404, "Execution not found.")
        return execution_view(execution)

    @app.get("/v1/usage")
    def usage(user: User = Depends(current_user), session: Session = Depends(db)):
        executions = session.scalars(
            select(Execution).where(
                Execution.user_id == user.id, Execution.finished_at.is_not(None)
            )
        ).all()
        seconds = sum(
            (e.finished_at - e.started_at).total_seconds() for e in executions if e.started_at
        )
        return {"executions": len(executions), "compute_seconds": round(seconds, 2)}

    return app


def app_factory() -> FastAPI:
    """Entry point for uvicorn: `uvicorn dataforge.main:app_factory --factory`."""
    return create_app()
