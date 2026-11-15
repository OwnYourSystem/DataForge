# Fast path: decisions that change specification v1.0

Date: 10 November 2026. Goal: a fast build that automation can test on each
commit. The original specification stays in this directory for reference.

## Decisions

| # | Specification v1.0 | Fast path | Reason |
|---|---|---|---|
| 1 | Azure foundation in week 1 | Cloud last | Subscriptions and approvals need people, not code |
| 2 | Databricks from day 1 | `dbt-duckdb` first, Databricks as a second adapter | The lesson runs in CI in seconds, at no cost |
| 3 | Tier B in the POC | Out of the POC | It is a second product |
| 4 | Service Bus, workflow engine, outbox, reconciler | Table `executions` is the queue; 1 worker | Sufficient for a pilot of 10 learners |
| 5 | 5 services, 5 packages, 4 images | `apps/api`, `apps/web`, `curriculum/` | Split when there is a reason |
| 6 | Infrastructure, then app, then grading | Lesson loop and grading first | You learn early if the lesson is good |
| 7 | Entra External ID | Dev header now; hosted provider for the pilot | `users.identity_subject` keeps the provider replaceable |

## Defects corrected

- **Token leak through Jinja.** `dataforge/guard.py` permits `source()` and
  `ref()` only. The learner cannot write `profiles.yml`, macros, or hooks.
- **Names.** The lesson id is `lab-001` and the operation id is `dbt_build`
  in the manifest, the API, and the UI.
- **Uploads.** There is no upload limit, because there are no uploads.
- **Entry point.** The worker image does not use `ENTRYPOINT ["dbt"]`. The
  worker calls dbt with fixed argument lists.

## Changes to LAB-001

- The seed data is now not clean (spaces, mixed case). With clean data, the
  grader could not detect a model without `trim`, `lower`, or `upper`.
- `dbt seed` and `dbt build` are 2 steps with 2 profile targets. The seed
  target can read the CSV file. The learner target has file access off.
- The grader gives no source credit for hardcoded rows.

## API differences from specification v1.0

- There is no sandbox resource. An execution gets a new workspace and a new
  DuckDB file, and the worker deletes them after the run. The route is
  `POST /v1/projects/{id}/executions`.
- Grading is part of the execution result. There is no `/v1/assessments`.
- The client polls `GET /v1/executions/{id}`. There is no SSE stream.
- Quota: 1 active execution for each user (HTTP 409 for a second one).

## Next steps

1. Sign-in: `DF_AUTH_MODE=jwt` with Supabase Auth is in the code. Connect a
   real project: see [../auth.md](../auth.md).
2. Databricks backend: the code is in `dataforge/backends/databricks.py`.
   Run the live test in [../databricks.md](../databricks.md) against a real
   workspace.
3. Alembic migrations, monthly quotas, then Tier B if a pilot shows the need.
