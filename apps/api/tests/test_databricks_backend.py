"""Databricks backend tests that need no workspace.

A fake connection takes the place of the SQL warehouse. The live test is in
test_databricks_live.py.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from conftest import LESSON, MODEL

from dataforge import grader, runner
from dataforge.backends.databricks import (
    ConfigError,
    Credential,
    DatabricksBackend,
    DatabricksSettings,
)

EXECUTION_ID = "7f6a1c35-fc50-4979-9187-27c879eac11a"
SCHEMA = "df_run_7f6a1c35fc504979918727c879eac11a"
ENV = {
    "DF_DBX_HOST": "https://adb-1234.5.azuredatabricks.net/",
    "DF_DBX_HTTP_PATH": "/sql/1.0/warehouses/abc123",
    "DF_DBX_CATALOG": "dataforge_lab",
    "DF_DBX_CLIENT_ID": "client-id-value",
    "DF_DBX_CLIENT_SECRET": "client-secret-value",
}


class FakeWarehouse:
    """Records SQL and returns rows for the first pattern that matches."""

    def __init__(self, responses=None):
        self.responses = responses or []
        self.statements: list[str] = []
        self.credentials: list[Credential] = []
        self.open = 0

    def connect(self, settings, credential):
        self.credentials.append(credential)
        self.open += 1
        return _FakeConnection(self)


class _FakeConnection:
    def __init__(self, warehouse):
        self.warehouse = warehouse

    def cursor(self):
        return _FakeCursor(self.warehouse)

    def close(self):
        self.warehouse.open -= 1


class _FakeCursor:
    def __init__(self, warehouse):
        self.warehouse = warehouse
        self.rows = None
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql):
        self.warehouse.statements.append(sql)
        for pattern, rows in self.warehouse.responses:
            if pattern in sql:
                if isinstance(rows, Exception):
                    raise rows
                self.rows, self.description = rows, [("c",)]
                return
        self.rows, self.description = None, None

    def fetchall(self):
        return self.rows


def make_backend(warehouse=None, **overrides):
    settings = DatabricksSettings.from_env({**ENV, **overrides})
    return DatabricksBackend(settings, connect=(warehouse or FakeWarehouse()).connect)


def test_settings_normalize_the_host():
    assert make_backend().settings.host == "adb-1234.5.azuredatabricks.net"


@pytest.mark.parametrize(
    "overrides",
    [
        {"DF_DBX_HOST": ""},
        {"DF_DBX_HOST": "host/with/path"},
        {"DF_DBX_HTTP_PATH": "no-leading-slash"},
        {"DF_DBX_CATALOG": "bad`; drop schema x cascade --"},
        {"DF_DBX_CATALOG": "Has-Dash"},
        {"DF_DBX_SCHEMA_PREFIX": "x'"},
        {"DF_DBX_CLIENT_SECRET": ""},
    ],
)
def test_bad_settings_are_rejected(overrides):
    with pytest.raises(ConfigError):
        make_backend(**overrides)


def test_each_execution_gets_its_own_schema(tmp_path):
    backend = make_backend()
    first = backend.new_context(EXECUTION_ID, tmp_path)
    second = backend.new_context("00000000-0000-4000-8000-000000000001", tmp_path)
    assert first.schema == SCHEMA
    assert first.schema != second.schema
    assert backend.relation(first, "stg_customers") == f"`dataforge_lab`.`{SCHEMA}`.`stg_customers`"
    with pytest.raises(ValueError):
        backend.new_context("not-a-uuid", tmp_path)


def test_profile_has_no_secret_values(lessons, tmp_path):
    backend = make_backend()
    ctx = backend.new_context(EXECUTION_ID, tmp_path)
    solution = (lessons[LESSON].root / "solution" / MODEL).read_text()
    runner.prepare_workspace(lessons[LESSON], {MODEL: solution}, backend, ctx)
    text = (tmp_path / "profiles.yml").read_text()
    assert "client-secret-value" not in text and "client-id-value" not in text
    output = yaml.safe_load(text)["retail_lakehouse"]["outputs"]["lab"]
    assert output["type"] == "databricks"
    assert output["catalog"] == "dataforge_lab" and output["schema"] == SCHEMA
    assert output["auth_type"] == "oauth"
    assert output["client_secret"] == "{{ env_var('DF_DBX_CLIENT_SECRET') }}"
    assert backend.env(ctx) == {
        "DF_DBX_CLIENT_ID": "client-id-value",
        "DF_DBX_CLIENT_SECRET": "client-secret-value",
    }


def test_token_auth_profile(tmp_path):
    backend = make_backend(DF_DBX_CLIENT_ID="", DF_DBX_CLIENT_SECRET="", DF_DBX_TOKEN="dapi-x")
    ctx = backend.new_context(EXECUTION_ID, tmp_path)
    output = backend.profile(ctx)["lab"]
    assert output["token"] == "{{ env_var('DF_DBX_TOKEN') }}" and "auth_type" not in output
    assert backend.env(ctx) == {"DF_DBX_TOKEN": "dapi-x"}
    assert "dapi-x" in backend.secrets()


def test_dbt_accepts_the_generated_project(lessons, tmp_path):
    """`dbt parse` needs no connection. It proves the profile and project are valid
    for dbt-databricks, and that the source points to the schema of the run."""
    backend = make_backend()
    ctx = backend.new_context(EXECUTION_ID, tmp_path)
    solution = (lessons[LESSON].root / "solution" / MODEL).read_text()
    runner.prepare_workspace(lessons[LESSON], {MODEL: solution}, backend, ctx)
    dbt = Path(sys.executable).parent / "dbt"
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), **backend.env(ctx)}
    done = subprocess.run(
        [str(dbt), "parse", "--profiles-dir", ".", "--no-use-colors", "--no-version-check"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    manifest = json.loads((tmp_path / "target" / "manifest.json").read_text())
    assert manifest["metadata"]["adapter_type"] == "databricks"
    source = manifest["sources"]["source.retail_lakehouse.retail_raw.raw_customers"]
    assert (source["database"], source["schema"]) == ("dataforge_lab", SCHEMA)
    model = manifest["nodes"]["model.retail_lakehouse.stg_customers"]
    assert (model["database"], model["schema"]) == ("dataforge_lab", SCHEMA)


def test_cleanup_drops_only_the_run_schema(tmp_path):
    warehouse = FakeWarehouse()
    backend = make_backend(warehouse)
    backend.cleanup(backend.new_context(EXECUTION_ID, tmp_path))
    assert warehouse.statements == [f"drop schema if exists `dataforge_lab`.`{SCHEMA}` cascade"]
    assert warehouse.open == 0


def test_sweep_drops_old_run_schemas_and_no_other_schema():
    warehouse = FakeWarehouse(
        [("information_schema.schemata", [("df_run_aaaa",), ("df_run_bbbb",)])]
    )
    backend = make_backend(warehouse)
    assert backend.sweep(max_age_minutes=30) == 2
    assert "startswith(schema_name, 'df_run_')" in warehouse.statements[0]
    assert "interval 30 minutes" in warehouse.statements[0]
    assert warehouse.statements[1:] == [
        "drop schema if exists `dataforge_lab`.`df_run_aaaa` cascade",
        "drop schema if exists `dataforge_lab`.`df_run_bbbb` cascade",
    ]


@pytest.mark.parametrize("name", ["default", "information_schema", "df_run_x`.`y", "prod"])
def test_sweep_refuses_a_schema_that_is_not_a_run_schema(name):
    warehouse = FakeWarehouse([("information_schema.schemata", [(name,)])])
    with pytest.raises(ValueError):
        make_backend(warehouse).sweep(max_age_minutes=30)
    assert not any(s.startswith("drop") for s in warehouse.statements)


def test_grader_uses_its_own_credential_when_one_is_set(tmp_path):
    warehouse = FakeWarehouse()
    backend = make_backend(
        warehouse, DF_DBX_GRADER_CLIENT_ID="grader-id", DF_DBX_GRADER_CLIENT_SECRET="grader-secret"
    )
    ctx = backend.new_context(EXECUTION_ID, tmp_path)
    with backend.grader_query(ctx) as query:
        query("select 1")
    backend.cleanup(ctx)
    assert [c.client_id for c in warehouse.credentials] == ["grader-id", "client-id-value"]
    assert "grader-secret" in backend.secrets()


GOOD_ROWS = [
    (1001, "Alice Jensen", "alice@example.com", "DENMARK"),
    (1002, "Daniel Smith", "daniel@example.com", "UNITED KINGDOM"),
    (1003, "Sara Nielsen", "sara@example.com", "DENMARK"),
    (1004, "Peter Hansen", "peter@example.com", "NORWAY"),
    (1005, "Maria Lopez", "maria@example.com", "SPAIN"),
]
GOOD_COLUMNS = [
    ("customer_key", "bigint"),
    ("customer_name", "string"),
    ("email", "string"),
    ("country", "string"),
    ("processed_at", "timestamp"),
]


def write_artifacts(workspace, model="success", tests="pass"):
    target = workspace / "target"
    target.mkdir()
    model_id = "model.retail_lakehouse.stg_customers"
    source_id = "source.retail_lakehouse.retail_raw.raw_customers"
    (target / "manifest.json").write_text(
        json.dumps({"nodes": {model_id: {"depends_on": {"nodes": [source_id]}}}})
    )
    results = [{"unique_id": model_id, "status": model}] + [
        {"unique_id": f"test.retail_lakehouse.t{i}", "status": tests} for i in range(3)
    ]
    (target / "run_results.json").write_text(json.dumps({"results": results}))


def grade_with(lessons, tmp_path, responses):
    warehouse = FakeWarehouse(responses)
    backend = make_backend(warehouse)
    ctx = backend.new_context(EXECUTION_ID, tmp_path)
    return grader.grade(lessons[LESSON], backend, ctx), warehouse


def test_grader_gives_full_score_for_correct_databricks_results(lessons, tmp_path):
    write_artifacts(tmp_path)
    result, warehouse = grade_with(
        lessons,
        tmp_path,
        [
            ("information_schema.columns", GOOD_COLUMNS),
            ("count(*)", [(5, 5, 0)]),
            ("select customer_key", GOOD_ROWS),
        ],
    )
    assert result["passed"] is True and result["score"] == 100
    assert all(SCHEMA in s for s in warehouse.statements)
    assert warehouse.open == 0


def test_grader_fails_wrong_databricks_values(lessons, tmp_path):
    write_artifacts(tmp_path)
    wrong = [(k, n, e, c.title()) for k, n, e, c in GOOD_ROWS]
    result, _ = grade_with(
        lessons,
        tmp_path,
        [
            ("information_schema.columns", GOOD_COLUMNS),
            ("count(*)", [(5, 5, 0)]),
            ("select customer_key", wrong),
        ],
    )
    assert result["passed"] is False and result["score"] == 70


def test_grader_does_not_pass_when_the_warehouse_is_not_available(lessons, tmp_path):
    write_artifacts(tmp_path)
    result, _ = grade_with(
        lessons, tmp_path, [("information_schema.columns", RuntimeError("warehouse stopped"))]
    )
    assert result["passed"] is False


def test_secrets_are_removed_from_learner_logs(tmp_path):
    backend = make_backend()
    text = runner._sanitize(
        f"error for client-secret-value in {tmp_path}/models", tmp_path, backend.secrets()
    )
    assert text == "error for [redacted] in /workspace/models"
    text = runner._sanitize(
        "probe to https://adb-1234.5.azuredatabricks.net/sql/1.0/warehouses/abc123 failed",
        tmp_path,
        backend.secrets(),
    )
    assert "azuredatabricks" not in text and "abc123" not in text
