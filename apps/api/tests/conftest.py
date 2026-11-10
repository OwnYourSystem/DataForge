import pytest
from fastapi.testclient import TestClient

from dataforge import curriculum
from dataforge.db import make_engine
from dataforge.main import create_app

LESSON = "lab-001"
MODEL = "models/staging/stg_customers.sql"


@pytest.fixture(scope="session")
def lessons():
    return curriculum.load_lessons()


@pytest.fixture()
def app(lessons):
    return create_app(engine=make_engine("sqlite:///:memory:"), lessons=lessons)


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def alice():
    return {"X-Dev-User": "alice"}


@pytest.fixture()
def bob():
    return {"X-Dev-User": "bob"}


@pytest.fixture()
def solution(lessons):
    return (lessons[LESSON].root / "solution" / MODEL).read_text()
