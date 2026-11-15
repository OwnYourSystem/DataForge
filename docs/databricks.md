# Databricks backend

The same lesson, runner, and grader run on Azure Databricks when
`DF_EXECUTION_BACKEND=databricks`. DuckDB stays the default and the backend
for CI.

**Status:** not yet run against a real workspace. The code is tested with
`dbt parse` and a fake SQL warehouse. The live test in step 3 is the proof.

## How a run works

Two service principals do the work. The reasons are in
[adr/004-run-isolation.md](adr/004-run-isolation.md).

1. The worker makes a schema name for the execution: `df_run_<32 hex>`.
2. The **platform principal** creates the schema and gives the **learner
   principal** `USE SCHEMA`, `CREATE TABLE` and `SELECT` on it.
3. The platform principal runs `dbt seed` to load the lesson data.
4. The learner principal runs `dbt build`: the learner model and the tests.
5. The grader reads the result as the platform principal.
6. The platform principal drops the schema. Every 10 minutes, a sweep drops
   run schemas that a stopped worker left.

Each query carries a comment with the execution id
(`dataforge_execution=<id>`), so that cost and duration in the Databricks
query history can be joined to one run.

Project files and progress are in Postgres, so no learner data stays in
Databricks after a run.

## Setup

### 1. Create the environment with Terraform

[../infra/README.md](../infra/README.md) has the steps. Terraform creates the
workspace, the catalog, the 2 kinds of principal, the grants, and the SQL
warehouse. There are no manual SQL steps.

### 2. Configuration

The Terraform outputs give these values.

| Variable | Value |
|---|---|
| `DF_EXECUTION_BACKEND` | `databricks` (API and worker) |
| `DF_DBX_HOST` | Output `df_dbx_host` |
| `DF_DBX_HTTP_PATH` | Output `df_dbx_http_path` |
| `DF_DBX_CATALOG` | Output `df_dbx_catalog` |
| `DF_DBX_PLATFORM_CLIENT_ID`, `DF_DBX_PLATFORM_CLIENT_SECRET` | Platform principal |
| `DF_DBX_LEARNER_CLIENT_ID`, `DF_DBX_LEARNER_CLIENT_SECRET` | Learner principal. A different one for each worker |
| `DF_EXECUTION_TIMEOUT_SECONDS` | `900`, so that a stopped warehouse can start |
| `DF_BACKEND_CALL_TIMEOUT_SECONDS` | Time limit for grading and for cleanup. Default `180` |

Only the worker needs the `DF_DBX_*` values. The API needs only
`DF_EXECUTION_BACKEND`, to check learner SQL in the Databricks dialect.

For a quick test, a personal access token also works: set
`DF_DBX_PLATFORM_TOKEN` and `DF_DBX_LEARNER_TOKEN`, and give the name of the
learner user in `DF_DBX_LEARNER_PRINCIPAL`. The 2 tokens must belong to 2
different identities.

Local stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.databricks.yml up --build
```

### 3. Live test

Add the `DF_DBX_*` values as repository secrets (Settings, Secrets and
variables, Actions). Then start the workflow **Databricks live test** from
the Actions tab. It runs the reference solution and an incorrect model,
checks that the run schemas are gone, and checks that the learner principal
cannot read outside its run schema.

## Isolation model and its limits

| Control | What it stops |
|---|---|
| Learner principal with rights on one run schema | Learner SQL cannot read a different run schema or other data. This is the primary control |
| One schema for each execution, dropped after grading | No results stay for a later run to read |
| Each dbt step gets one credential | The learner step does not hold the platform secret |
| Learner SQL guard (`dataforge/guard.py`) | A second control: one `select`, only `source()` and `ref()` relations |
| Function deny list | `secret()`, `ai_*`, `http_*`, `read_*`, `reflect()` and similar functions |
| Jinja guard and secrets in the environment only | The learner cannot read an OAuth secret |

Limits you must know:

- **One learner principal for each worker.** A worker runs one execution at
  a time. If 2 workers share a learner principal, a run can have rights on 2
  run schemas, and the isolation then depends on the SQL guard again.
- The warehouse is shared, so one heavy query can slow other learners.
- Cost control is the warehouse size and auto-stop time, plus the quota of
  1 active execution for each user. There is no budget cap in the app yet.
- The full list of threats and gaps is in [threat-model.md](threat-model.md).
