# Databricks backend

The same lesson, runner, and grader run on Azure Databricks when
`DF_EXECUTION_BACKEND=databricks`. DuckDB stays the default and the backend
for CI.

**Status:** not yet run against a real workspace. The code is tested with
`dbt parse` and a fake SQL warehouse. The live test in step 5 is the proof.

## How a run works

1. The worker makes a schema name for the execution: `df_run_<32 hex>`.
2. `dbt seed` loads the lesson data. dbt creates the schema.
3. `dbt build` runs the learner model and the tests in that schema.
4. The grader reads the result through a SQL connection.
5. The worker drops the schema. Every 10 minutes, a sweep drops run schemas
   that a stopped worker left.

Project files and progress are in Postgres, so no learner data stays in
Databricks after a run.

## Setup

You need a workspace with Unity Catalog and a SQL warehouse. A serverless
warehouse with a short auto-stop time gives the lowest cost and the
shortest start time.

### 1. Catalog

```sql
CREATE CATALOG IF NOT EXISTS dataforge_lab;
```

Use this catalog for run schemas only.

### 2. Service principals

Make 2 service principals in the workspace and make an OAuth secret for
each one:

- `dataforge-runner` runs dbt.
- `dataforge-grader` reads results. It is optional but recommended.

Use Databricks OAuth secrets (machine-to-machine). The backend also accepts
a personal access token in `DF_DBX_TOKEN`, for a quick test only.

### 3. Grants

```sql
GRANT USE CATALOG, CREATE SCHEMA ON CATALOG dataforge_lab TO `<runner application id>`;
GRANT USE CATALOG, USE SCHEMA, SELECT ON CATALOG dataforge_lab TO `<grader application id>`;
```

The runner owns the schemas it makes, so it can drop them. Give each
principal **Can use** on the SQL warehouse. Give them no other rights: no
secret scopes, no external locations, no other catalogs.

### 4. Configuration

| Variable | Value |
|---|---|
| `DF_EXECUTION_BACKEND` | `databricks` (API and worker) |
| `DF_DBX_HOST` | Workspace host, for example `adb-123.4.azuredatabricks.net` |
| `DF_DBX_HTTP_PATH` | HTTP path of the SQL warehouse |
| `DF_DBX_CATALOG` | `dataforge_lab` |
| `DF_DBX_CLIENT_ID`, `DF_DBX_CLIENT_SECRET` | Runner principal |
| `DF_DBX_GRADER_CLIENT_ID`, `DF_DBX_GRADER_CLIENT_SECRET` | Grader principal (optional) |
| `DF_EXECUTION_TIMEOUT_SECONDS` | `900`, so that a stopped warehouse can start |
| `DF_BACKEND_CALL_TIMEOUT_SECONDS` | Time limit for grading and for cleanup. Default `180` |

Only the worker needs the `DF_DBX_*` values. The API needs only
`DF_EXECUTION_BACKEND`, to check learner SQL in the Databricks dialect.

Local stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.databricks.yml up --build
```

### 5. Live test

Add the `DF_DBX_*` values as repository secrets (Settings, Secrets and
variables, Actions). Then start the workflow **Databricks live test** from
the Actions tab. It runs the reference solution and an incorrect model, and
it checks that the run schemas are gone.

## Isolation model and its limits

One runner principal runs the SQL of all learners. These controls keep
learners apart:

| Control | What it stops |
|---|---|
| Learner SQL guard (`dataforge/guard.py`) | A model can read only `source()` and `ref()` relations. It cannot name a different schema, `information_schema`, a file path, or a table function. |
| Function deny list | `secret()`, `ai_*`, `http_*`, `read_*`, `reflect()` and similar functions. |
| One schema for each execution, dropped after grading | Results of a different learner are not there to read, except during a run at the same time. |
| Grants in the lab catalog only | The principal cannot reach other data in the workspace. |
| Jinja guard and secrets in the environment only | The learner cannot read the OAuth secret. |

Limits you must know:

- The SQL guard is a parser check. It is a second control, not a
  replacement for grants. For a public launch, use one principal for each
  learner, or one workspace for each cohort.
- The warehouse is shared, so one heavy query can slow other learners.
  Set a statement timeout on the warehouse.
- Cost control is the warehouse size and auto-stop time, plus the quota of
  1 active execution for each user. There is no budget cap in the app yet.
