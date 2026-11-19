# ADR-005: From learning portal to change-impact tool

Date: 19 November 2026
Status: accepted
Replaces: the learning-portal direction in `docs/spec/fast-path.md` and the
goals and roadmap in `docs/spec/platform-proof-track.md`. Replaces ADR-004 in
part.

## Context

The first version of DataForge was a learning portal: a learner wrote a dbt
model in the browser, and a grader checked the result. On 19 November 2026
the direction was tested against 2 questions:

1. **Is there a market?** Free training (Databricks Academy, dbt Learn) is
   strong, and private learners pay little.
2. **What problem is worth the work?** Research tested the thesis that the
   hardest part of data engineering is keeping data correct across teams that
   do not own each other's systems. The result was "partly supported":
   cross-team correctness is a large and lasting problem, but not shown to be
   the hardest one.

## Decision

DataForge becomes a **read-only, metadata-only tool** that finds changes that
cross an ownership boundary (Terraform, Unity Catalog, dbt) and tells the
owners on the other side, in the pull request.

The full description is in [../overview.md](../overview.md).

### What stays

| Part | New role |
|---|---|
| Terraform for Azure Databricks (ADR-001) | The reference platform that DataForge is tested against |
| Separate identities with separate rights (ADR-004) | The model for read-only collector credentials |
| FastAPI, Postgres, worker queue | Graph store and job runner for collectors |
| CI, ADRs, threat model | Kept. The threat model is rewritten for metadata-only access |

### What stops

- The lab editor, labs, scoring, and learner sign-in.
- The live portal on Render and its Supabase project.
- The flyer and the marketing for learners.
- LAB-001 stays in the repository as an archived demo. It is not developed.

### Rules that change

| Rule | Before | After |
|---|---|---|
| 3 | Platform before product | Problem before product: product features wait until a design partner has run DataForge on a real repository |
| 4 | Trusted and untrusted code stay apart | Metadata only, read-only: DataForge never reads rows and never writes to a client platform |
| 6 | DuckDB stays the CI default | Offline tests with recorded metadata fixtures stay the CI default |
| 9 (new) | | Measure the problem, not only the tool |

## Alternatives

- **Continue the learning portal.** Rejected for the reasons in "Context".
- **A full data catalog or a data observability tool.** Rejected. These
  markets are crowded, and they need row access, which rule 4 forbids.
- **A consulting method with no software.** Kept as the fallback if the
  second kill criterion fails (no design partners by week 10).

## Consequences

- **The value of the problem is not yet proven.** Desk research
  ([../research/method.md](../research/method.md)) must pass its gate before
  Phase 2. If it fails, DataForge stays a portfolio project.
- **Neighbors are close.** Datafold, Recce, dbt contracts, Gable, the Data
  Contract CLI, and Unity Catalog lineage each cover part of the problem. The
  research must show a gap.
- **Owner tagging is the main setup cost** for a client, and it is an
  organization task, not a tool task.
- **Changes in meaning are out of scope.** Metadata cannot see them. Every
  blueprint must state this limit.
- **The learner principal in the Terraform is not needed.** Phase 1 replaces
  it with a read-only collector principal.
