# ADR-004: Two kinds of service principal for run isolation

Date: 15 November 2026
Status: accepted. Replaced in part by [ADR-005](005-change-impact-tool.md) on 19 November 2026:
there are no learners, so the learner principal is not needed. The model of
separate identities with separate rights stays, for the read-only collectors.
Replaces: the "one runner principal" model in the first Databricks backend

## Context

The first Databricks backend used one service principal for all work. It
made each run schema, ran the learner SQL, and dropped the schema. So the
identity that ran learner SQL owned all run schemas and could read all of
them. Only the SQL guard kept learners apart.

This fails two requirements of the platform track:

- Rule 4: learner code never runs with platform credentials.
- Phase 1: a test shows that the learner principal cannot read outside its
  run schema.

## Decision

Two kinds of principal, with different rights.

| | Platform principal | Learner principal |
|---|---|---|
| Trusted | Yes | No |
| Number | 1 | 1 for each worker |
| Catalog rights (Terraform) | `USE_CATALOG`, `USE_SCHEMA`, `CREATE_SCHEMA`, `SELECT` | `USE_CATALOG` |
| Run schema rights | Owner | `USE SCHEMA`, `CREATE TABLE`, `SELECT`, given at the start of the run |
| Runs | Schema creation, lesson data load, grading, cleanup, sweep | The learner model and its tests |

One run goes like this:

1. Platform: `create schema`, then `grant ... to <learner principal>`.
2. Platform: `dbt seed` loads the lesson data. The learner principal can
   read it, and cannot change it.
3. Learner: `dbt build` runs the learner model. The tables it makes belong
   to the learner principal.
4. Platform: the grader reads the result.
5. Platform: `drop schema ... cascade`. The grants go with the schema.

Each dbt step gets a profile with one target and an environment with one
credential. The learner step does not hold the platform secret.

**One learner principal for each worker.** A worker runs one execution at a
time. So a learner principal has rights on one run schema at a time, and
the isolation does not depend on the SQL guard. To run 3 executions at the
same time, use 3 workers and set `learner_count = 3` in Terraform.

## Alternatives

- **One principal for each learner.** The strongest model, and the correct
  one for a public service with many learners. It needs identity lifecycle
  work for each sign-up. Not necessary while runs use a new schema each time.
- **One principal for each run.** Strong, but each run then needs an
  identity API call and a new OAuth secret. Slow and hard to clean up.
- **Keep one principal and trust the SQL guard.** Rejected. A parser check
  is a second control, not the first one.

## Consequences

- The backend needs 2 sets of credentials: `DF_DBX_PLATFORM_*` and
  `DF_DBX_LEARNER_*`. The old `DF_DBX_CLIENT_ID` settings are removed.
- The SQL guard stays, as defence in depth.
- More workers need more learner principals.

## To verify in the live test

These points depend on Unity Catalog behaviour that the offline tests cannot
show:

1. dbt, as the learner principal, works in a schema that exists already,
   with no right to create a schema.
2. The platform principal, as owner of the schema, can drop it with
   `cascade` when the tables in it belong to the learner principal. If not,
   add `MANAGE` on the catalog for the platform principal.
3. The learner principal cannot see a different run schema in
   `information_schema`.

`apps/api/tests/test_databricks_live.py` has a test for points 1 and 3, and
each live test checks point 2.
