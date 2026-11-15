"""Live test against a real Azure Databricks SQL warehouse.

It runs only when DF_DBX_HOST is set. See docs/databricks.md for the setup.
It runs the same path as a learner execution: seed, build, grade, cleanup.
"""

import os
import uuid

import pytest
from conftest import LESSON, MODEL

from dataforge import grader, runner

pytestmark = pytest.mark.skipif(
    not os.environ.get("DF_DBX_HOST"), reason="no Databricks workspace is configured"
)

TIMEOUT_SECONDS = 900  # a stopped warehouse must start first


@pytest.fixture(scope="module")
def backend():
    from dataforge.backends.databricks import DatabricksBackend, DatabricksSettings

    return DatabricksBackend(DatabricksSettings.from_env())


def execute(backend, lessons, tmp_path, sql):
    ctx = backend.new_context(str(uuid.uuid4()), tmp_path)
    try:
        runner.prepare_workspace(lessons[LESSON], {MODEL: sql}, backend, ctx)
        backend.prepare(ctx)
        result = runner.dbt_build(backend, ctx, TIMEOUT_SECONDS)
        assessment = grader.grade(lessons[LESSON], backend, ctx)
    finally:
        backend.cleanup(ctx)
    return ctx, result, assessment


def schema_exists(backend, schema):
    catalog = backend.settings.catalog
    with backend._query(backend.settings.platform) as query:
        rows = query(
            f"select 1 from `{catalog}`.information_schema.schemata where schema_name = '{schema}'"
        )
    return bool(rows)


def test_reference_solution_passes_and_the_schema_is_removed(backend, lessons, tmp_path):
    solution = (lessons[LESSON].root / "solution" / MODEL).read_text()
    ctx, result, assessment = execute(backend, lessons, tmp_path, solution)
    assert result.status == "succeeded", result.logs
    assert assessment["score"] == 100 and assessment["passed"] is True, assessment
    for secret in backend.secrets():
        assert secret not in result.logs
    assert not schema_exists(backend, ctx.schema)


def test_incorrect_transformation_fails_grading(backend, lessons, tmp_path):
    solution = (lessons[LESSON].root / "solution" / MODEL).read_text()
    wrong = solution.replace("upper(trim(country))", "trim(country)")
    ctx, result, assessment = execute(backend, lessons, tmp_path, wrong)
    assert result.status == "succeeded", result.logs
    assert assessment["passed"] is False and assessment["score"] == 70, assessment
    assert not schema_exists(backend, ctx.schema)


def test_learner_principal_cannot_read_outside_its_run_schema(backend, lessons, tmp_path):
    """Phase 1 acceptance test. The SQL guard is off here: only the grants of
    the learner principal stand between a learner and other data."""
    other = backend.new_context(str(uuid.uuid4()), tmp_path / "other")
    mine = backend.new_context(str(uuid.uuid4()), tmp_path / "mine")
    catalog = backend.settings.catalog
    attempts = {
        "a table in the schema of a different run": (
            f"select * from `{catalog}`.`{other.schema}`.`secret_table`"
        ),
        "the list of schemas in the catalog": (
            f"select schema_name as customer_key from `{catalog}`.information_schema.schemata "
            f"where schema_name = '{other.schema}'"
        ),
    }
    try:
        # The other run: a schema that the learner principal has no rights on.
        with backend._query(backend.settings.platform) as query:
            query(f"create schema `{catalog}`.`{other.schema}`")
            query(f"create table `{catalog}`.`{other.schema}`.`secret_table` as select 42 as n")
        for name, sql in attempts.items():
            workspace = tmp_path / name.replace(" ", "_")
            workspace.mkdir()
            ctx = backend.new_context(str(uuid.uuid4()), workspace)
            try:
                runner.prepare_workspace(lessons[LESSON], {MODEL: sql}, backend, ctx, guard=False)
                backend.prepare(ctx)
                result = runner.dbt_build(backend, ctx, TIMEOUT_SECONDS)
                with backend.grader_query(ctx) as query:
                    try:
                        rows = query(f"select * from {backend.relation(ctx, 'stg_customers')}")
                    except Exception:
                        rows = []
            finally:
                backend.cleanup(ctx)
            assert rows == [] or result.status == "failed", f"the learner principal read {name}"
            assert "42" not in result.logs
        # The learner principal cannot make a schema.
        with pytest.raises(Exception):  # noqa: B017 - the engine error type is not stable
            with backend._query(backend.settings.learner) as query:
                query(f"create schema `{catalog}`.`{mine.schema}`")
    finally:
        with backend._query(backend.settings.platform) as query:
            query(f"drop schema if exists `{catalog}`.`{other.schema}` cascade")
            query(f"drop schema if exists `{catalog}`.`{mine.schema}` cascade")
