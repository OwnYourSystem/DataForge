# Threat model

> **Written for the learning portal.** On 19 November 2026 DataForge became a
> read-only, metadata-only tool ([ADR-005](adr/005-change-impact-tool.md)).
> This model is rewritten in Phase 1 for metadata-only access. Until then, it
> describes the archived lab.

Date: 15 November 2026. Update this file in each phase of the platform track.

## What we protect

| Asset | Why it matters |
|---|---|
| Platform credentials | Database address, platform principal secret, Terraform state |
| Other learners' work | Model files, results, scores |
| Reference solutions and the grader | A leak makes a pass worth nothing |
| Cloud cost | A learner must not be able to run up a bill |
| Other data in the cloud account | The lab must not be a way in |

## Who we defend against

A signed-in learner who sends hostile SQL or hostile requests. We do not
defend against a person who controls the cloud account or the repository.

## Trust boundaries

```text
Browser (not trusted)
  -> Web server and API (trusted, hold the database address)
       -> Worker (trusted code, runs dbt for learner SQL)
            -> SQL engine (learner SQL runs here)
```

Learner input is: the content of 1 SQL file, and the id of an approved
operation. Nothing else from the learner reaches the worker.

## Threats and controls

| # | Threat | Control | Where | Tested |
|---|---|---|---|---|
| 1 | Run a shell command | The learner sends an operation id. Commands are fixed lists | `runner.py` | Yes |
| 2 | Change trusted dbt files (profile, macros, tests) | Exact allowlist of editable paths | `main.py` | Yes |
| 3 | Read a secret through Jinja (`env_var`) | Only `source()` and `ref()` are permitted | `guard.py` | Yes |
| 4 | Read a secret from the process environment | dbt gets a minimal environment. Each step gets one credential | `runner.py` | Yes |
| 5 | Read files on the worker (DuckDB) | File access is off for learner SQL | `backends/duckdb.py` | Yes |
| 6 | Read the tables of a different run (Databricks) | The learner principal has rights on one run schema | `backends/databricks.py`, `infra/` | Offline yes. Live: not yet |
| 7 | Read other data in the workspace | The learner principal has `USE_CATALOG` on the lab catalog only | `infra/modules/unity-catalog` | Live: not yet |
| 8 | Call secrets, network, or AI functions in SQL | Function deny list. The principal has no secret scope | `guard.py` | Yes (guard) |
| 9 | More than one statement, or DDL | One `select` only | `guard.py` | Yes |
| 10 | See the solution | Not in the runtime images. Never sent by the API | `.dockerignore`, CI | Yes |
| 11 | Forge a grade | The grader reads the real table and calculates expected values | `grader.py` | Yes |
| 12 | Act as a different learner | Signed tokens, asymmetric keys only. Owner check on each request | `auth.py`, `main.py` | Yes |
| 13 | Use many runs to make cost | One active run for each user. Small warehouse, 1 cluster, auto-stop | `main.py`, `infra/modules/sql-warehouse` | Quota yes. Cost: not yet |
| 14 | A run that does not end | Time limit on dbt, on grading, and on cleanup | `runner.py`, `worker.py` | Yes |
| 15 | Leave resources after a crash | A sweep drops old run schemas | `backends/databricks.py` | Offline yes |
| 16 | Read the Terraform state | State storage has no access keys, Entra sign-in only | `infra/bootstrap` | Not yet |

## Known gaps

1. **The free Render deployment runs dbt in the API container.** Controls 3,
   4 and 5 still apply, but the worker is not a separate machine. This
   layout is for trusted people only. See `docs/deploy.md`.
2. **No budget cap in the app.** Control 13 limits the rate, not the total.
   Phase 4 adds cost alerts.
3. **No statement time limit on the warehouse.** The dbt time limit stops the
   client. A long query can continue on the warehouse for a short time.
4. **No audit trail in the app.** The `executions` table records each run
   and its owner, but not sign-ins or file changes. Databricks system tables
   give the engine side. Phase 4.
5. **Sign-up is open** in the Supabase project.
6. **Controls 6, 7 and 16 are not proven live.** They need the Azure
   environment.
