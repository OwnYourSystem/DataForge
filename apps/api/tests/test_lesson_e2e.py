"""The full lesson loop with real dbt on DuckDB: save, run, grade, progress."""

import os

import pytest
from conftest import LESSON, MODEL

from dataforge import runner, worker
from dataforge.backends.duckdb import DuckDBBackend

SOURCE = "{{ source('retail_raw', 'raw_customers') }}"


def run(client, app, lessons, headers, sql, backend=None):
    backend = backend or DuckDBBackend()
    project = client.post("/v1/projects", json={"lesson_id": LESSON}, headers=headers).json()["id"]
    put = client.put(
        f"/v1/projects/{project}/files/{MODEL}", json={"content": sql}, headers=headers
    )
    assert put.status_code == 200, put.text
    queued = client.post(
        f"/v1/projects/{project}/executions", json={"operation_id": "dbt_build"}, headers=headers
    ).json()
    assert worker.run_once(app.state.session_factory, lessons, 120, backend)
    result = client.get(queued["status_url"], headers=headers).json()
    return project, result


def checks(result):
    return {c["id"]: c["passed"] for c in result["assessment"]["checks"]}


def test_reference_solution_passes_with_full_score(client, app, lessons, alice, solution):
    project, result = run(client, app, lessons, alice, solution)
    assert result["status"] == "succeeded", result["logs"]
    assert result["assessment"]["passed"] is True
    assert result["assessment"]["score"] == 100
    assert result["compute_seconds"] > 0
    progress = client.get(f"/v1/projects/{project}", headers=alice).json()
    assert progress["best_score"] == 100 and progress["completed_at"]
    assert client.get("/v1/usage", headers=alice).json()["executions"] == 1


def test_starter_file_does_not_pass(client, app, lessons, alice):
    starter = lessons[LESSON].starter_files()[MODEL]
    project, result = run(client, app, lessons, alice, starter)
    assert result["assessment"]["passed"] is False
    assert checks(result)["transformations"] is False
    assert client.get(f"/v1/projects/{project}", headers=alice).json()["completed_at"] is None


def test_incorrect_transformation_fails_grading(client, app, lessons, alice, solution):
    wrong = solution.replace("upper(trim(country))", "trim(country)")
    _, result = run(client, app, lessons, alice, wrong)
    assert result["status"] == "succeeded"  # dbt is satisfied, the grader is not
    assert checks(result)["transformations"] is False
    assert result["assessment"]["score"] == 70
    assert result["assessment"]["passed"] is False


def test_hardcoded_rows_do_not_get_source_credit(client, app, lessons, alice):
    sql = (
        "select * from (values (cast(1001 as bigint), 'Alice Jensen', 'alice@example.com',"
        " 'DENMARK', current_timestamp)) t(customer_key, customer_name, email, country,"
        " processed_at)"
    )
    _, result = run(client, app, lessons, alice, sql)
    assert checks(result)["source-reference"] is False
    assert result["assessment"]["passed"] is False


def test_sql_error_gives_failed_status_and_clean_logs(client, app, lessons, alice):
    _, result = run(client, app, lessons, alice, f"select no_such_column from {SOURCE}")
    assert result["status"] == "failed"
    assert result["assessment"]["passed"] is False
    assert "no_such_column" in result["logs"]
    assert "df-run-" not in result["logs"]  # no worker paths in learner logs


def run_without_guard(lessons, tmp_path, sql):
    """Run SQL that the guard rejects, to test the engine controls under it."""
    backend = DuckDBBackend()
    ctx = backend.new_context("00000000-0000-0000-0000-000000000000", tmp_path)
    runner.prepare_workspace(lessons[LESSON], {MODEL: sql}, backend, ctx, guard=False)
    return runner.dbt_build(backend, ctx, 120)


def test_engine_stops_file_reads_if_the_guard_is_bypassed(lessons, tmp_path):
    sql = (
        f"select customer_id as customer_key, content as email from {SOURCE}, "
        "read_text('/etc/hostname')"
    )
    result = run_without_guard(lessons, tmp_path, sql)
    assert result.status == "failed"
    assert "file system operations are disabled" in result.logs


def test_worker_environment_does_not_reach_dbt(lessons, tmp_path, monkeypatch):
    monkeypatch.setenv("DF_TEST_SECRET", "s3cr3t-value")
    sql = f"select getenv('DF_TEST_SECRET') as customer_key, 'x' as email from {SOURCE}"
    result = run_without_guard(lessons, tmp_path, sql)
    assert "s3cr3t-value" not in result.logs


def test_worker_checks_the_guard_again_before_a_run(client, app, lessons, alice):
    """A file that did not go through the API guard is stopped in the worker."""
    from sqlalchemy import update

    from dataforge.db import Execution

    project = client.post("/v1/projects", json={"lesson_id": LESSON}, headers=alice).json()["id"]
    queued = client.post(
        f"/v1/projects/{project}/executions", json={"operation_id": "dbt_build"}, headers=alice
    ).json()
    with app.state.session_factory() as session:
        session.execute(
            update(Execution)
            .where(Execution.id == queued["id"])
            .values(files={MODEL: "select * from other_schema.stg_customers"})
        )
        session.commit()
    assert worker.run_once(app.state.session_factory, lessons, 120, DuckDBBackend())
    result = client.get(queued["status_url"], headers=alice).json()
    assert result["status"] == "failed"
    assert "source() or ref()" in result["logs"]
    assert result["assessment"] is None


def test_backend_cleanup_runs_after_a_failed_run(client, app, lessons, alice):
    class Spy(DuckDBBackend):
        cleaned: list[str] = []

        def cleanup(self, ctx):
            self.cleaned.append(ctx.execution_id)

    spy = Spy()
    _, result = run(client, app, lessons, alice, f"select no_such_column from {SOURCE}", spy)
    assert result["status"] == "failed"
    assert spy.cleaned == [result["id"]]


def test_workspace_is_removed_after_the_run(
    client, app, lessons, alice, solution, tmp_path, monkeypatch
):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    run(client, app, lessons, alice, solution)
    assert os.listdir(tmp_path) == []


def test_time_limit_gives_timed_out(client, app, lessons, alice, solution):
    project = client.post("/v1/projects", json={"lesson_id": LESSON}, headers=alice).json()["id"]
    client.put(f"/v1/projects/{project}/files/{MODEL}", json={"content": solution}, headers=alice)
    queued = client.post(
        f"/v1/projects/{project}/executions", json={"operation_id": "dbt_build"}, headers=alice
    ).json()
    assert worker.run_once(app.state.session_factory, lessons, 0, DuckDBBackend())
    result = client.get(queued["status_url"], headers=alice).json()
    assert result["status"] == "timed_out"
    assert result["assessment"] is None


@pytest.mark.parametrize("workers", [2])
def test_an_execution_is_claimed_one_time_only(client, app, lessons, alice, workers):
    project = client.post("/v1/projects", json={"lesson_id": LESSON}, headers=alice).json()["id"]
    client.post(
        f"/v1/projects/{project}/executions", json={"operation_id": "dbt_build"}, headers=alice
    )
    factory = app.state.session_factory
    claims = [worker.claim_next(factory) for _ in range(workers)]
    assert sum(c is not None for c in claims) == 1


def test_a_backend_that_does_not_answer_cannot_stop_the_worker(
    client, app, lessons, alice, solution, monkeypatch
):
    import threading
    from contextlib import contextmanager

    release = threading.Event()

    class Stuck(DuckDBBackend):
        @contextmanager
        def grader_query(self, ctx):
            release.wait(30)
            yield lambda sql: []

    monkeypatch.setenv("DF_BACKEND_CALL_TIMEOUT_SECONDS", "1")
    try:
        _, result = run(client, app, lessons, alice, solution, Stuck())
    finally:
        release.set()
    assert result["status"] == "failed"
    assert result["assessment"] is None
    assert "grader did not answer" in result["logs"]
