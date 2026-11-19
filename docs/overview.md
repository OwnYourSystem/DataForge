# DataForge

**Know who you will break before you merge.**

Status on 19 November 2026. This page is the short description of the whole
project after the redesign: what it is, why it changed, how it connects to a
client platform, where it goes, and what is true today.

The description of the first version (the learning portal) is archived in
[spec/learning-portal-overview.md](spec/learning-portal-overview.md). The
decision is [ADR-005](adr/005-change-impact-tool.md).

---

## 1. What DataForge is

DataForge finds changes that cross an ownership boundary on a data platform,
before they break data that another team depends on.

It reads metadata from 4 layers:

| Layer | What DataForge reads |
|---|---|
| Terraform | Plans and state: workspaces, catalogs, schemas, identities, grants |
| Azure | Resource configuration that Terraform does not own |
| Databricks Unity Catalog | Tables, columns, grants, tags, lineage, table history |
| dbt | `manifest.json`: sources, models, contracts, owners, exposures |

DataForge joins these layers into 1 graph. Each node has an owner. When a
change arrives (a pull request, a Terraform plan, a new dbt manifest, a schema
change on an ingested table), DataForge finds what is downstream, finds who
owns it, and tells those owners.

DataForge reads metadata only. It never reads rows of data.

DataForge is still built in the open. Each phase ends with a published
blueprint.

---

## 2. Why the direction changed

The first version was a learning portal with hands-on labs. That direction is
stopped. The reasons:

1. Free training (Databricks Academy, dbt Learn) is strong, and private
   learners pay little.
2. Research on 19 November 2026 tested this thesis: *the hardest part of data
   engineering is keeping data correct across teams that do not own each
   other's systems.* The verdict was **partly supported**:
   - **Supported:** cross-team correctness is a large and lasting problem.
     Unclear ownership is a top pain point in 3 surveys (39% to 51%).
   - **Not supported:** that it is *the* hardest problem.
   - **Measured:** source-side causes (ingestion disruptions and schema drift)
     are about 24% of incidents in the only root-cause data we found. That data
     comes from a vendor, so treat it as an estimate.

   **The sources of these numbers are not yet in the repository.** They go
   in [research/](research/) with the desk research (see section 11). Do not
   publish the numbers before then (rule 1).
   - **Pattern:** ingestion is where these failures show first and loudest.
     Disagreements about meaning are where they cost most.

DataForge now works on the supported part only: changes at ownership
boundaries.

---

## 3. The problem

On a shared platform, 1 team changes something and another team finds out when
its data is wrong. Examples:

- A source team renames a column. The ingestion pipeline needs a full refresh,
  and a dbt model fails 2 layers later.
- A platform team changes a grant in Terraform. A consumer job loses access at
  night.
- An analytics team changes a dbt model that a finance report uses. Nobody in
  finance is told.

Each tool sees its own layer. dbt sees dbt. Unity Catalog sees tables and
lineage. Terraform sees infrastructure. Nobody sees the change *and* the owner
on the other side of the boundary.

---

## 4. The position

DataForge does **not** compete as a data catalog, a data observability tool,
or a data contract standard.

The position is: **ownership-aware change impact across Terraform, Unity
Catalog, and dbt.** DataForge answers 1 question well: *if this change merges,
which other teams are affected, and who must be told?*

For regulated companies, the same record is evidence of controlled change.
Regulations such as DORA ask for this. DataForge is not a compliance product.
It produces evidence that a compliance process can use.

---

## 5. Goals

### Goal 1: a working change-impact tool

A platform team must be able to:

1. Run DataForge as a CLI or a GitHub Action, with read-only credentials.
2. See the cross-layer graph with an owner on each node.
3. Get a comment on each pull request that lists breaking changes, affected
   assets, and their owners.
4. Get an alert when a source table changes after the fact.
5. Tag each data incident by cause: another team's change, an internal fault,
   or not a real error.

### Goal 2: public proof (kept from the first version)

| Aim | What DataForge must prove |
|---|---|
| Career | Platform engineering, Terraform, dbt, Databricks, Azure, CI/CD, observability, Data Mesh |
| Brand (OwnYourSystem) | Authority on ownership boundaries and controlled change, through blueprints and a field report |
| Consulting | A concrete tool and method that OYS can use with clients in regulated Nordic finance |

The flow of value is now: **build, then blueprint, then field report.**

---

## 6. Rules

Rules 1, 2, 5, 7, and 8 stay. Rules 3, 4, and 6 change. Rule 9 is new.

1. **Proof before publication.** No blueprint or claim describes a feature that
   does not run live, with the evidence in the repository.
2. **1 milestone, 1 blueprint.**
3. **Problem before product.** Product features wait until a design partner
   has run DataForge on a real repository. *(Was: platform before product.)*
4. **Metadata only, read-only.** DataForge never reads rows and never writes to
   a client platform. *(Was: trusted and untrusted code stay apart.)*
5. **Everything as code.**
6. **Offline tests stay the CI default.** CI uses recorded metadata fixtures
   and needs no cloud account. Cloud runs are extra proof. *(Was: DuckDB stays
   the CI default.)*
7. **Clean-room only.** No code, data, or names from an employer.
8. **Write down decisions** as ADRs.
9. **Measure the problem, not only the tool.** Every phase records evidence on
   how often boundary changes cause incidents.

---

## 7. Scope of version 1

Version 1 does 1 thing: **a breaking-change check in CI, with owners.**

| In version 1 | Not in version 1 |
|---|---|
| dbt manifest and Unity Catalog metadata | Data quality checks on rows |
| Terraform plan for grants, schemas, identities | Changes in meaning (definitions, metric logic) |
| Owners from dbt `meta`, Unity Catalog tags, CODEOWNERS | A full data catalog UI |
| A gap list of assets with no owner | Hosted (SaaS) deployment |
| PR comment and CLI report | Automatic blocking of merges |
| Azure Databricks | AWS, Snowflake, Fabric |

Changes in meaning are the most expensive class of boundary problem. They are
out of scope because metadata cannot see them. This limit is stated in every
blueprint.

---

## 8. How it is built

```text
GitHub Action / CLI
  └── Collectors (read-only): Terraform plan, Unity Catalog, dbt manifest, Azure
        └── Graph builder: 1 graph, owner on each node, snapshot per change
              └── Postgres: snapshots, diffs, owners, incident tags
                    └── Impact engine: diff, classify, find downstream owners
                          └── Outputs: PR comment, CLI report, alert, read-only web view
```

### What is reused from the first version

| First version | New role |
|---|---|
| Terraform for Azure Databricks and Unity Catalog | The reference platform that DataForge is tested against |
| 2 identities with separate rights | The model for read-only collector credentials |
| Independent grader that reads the real table | The verifier that compares a contract with the live table schema (column names and types). It never reads rows (rule 4) |
| FastAPI API, Postgres, worker queue | Graph store and job runner for collectors |
| DuckDB CI | Offline tests with recorded metadata fixtures |
| Next.js portal | A small read-only view of the graph. The editor is removed |
| Threat model and ADRs | Kept and updated for metadata-only access |

### What is removed

- The lab editor, labs, scoring, and learner sign-in.
- LAB-001 stays in the repository as an archived demo. It is not developed.

### Security model

- Collectors use read-only identities with metadata rights only.
- No row data leaves the client platform.
- Secrets stay in the CI system of the client.
- Each collector gets only its own credential.

---

## 9. How it connects to a client platform

DataForge does nothing until it is connected. It does not ask the client to
move to a new system. It runs **inside the pipelines the client already has**.

### Integration points

| Client system | How DataForge connects | New access needed |
|---|---|---|
| GitHub or Azure DevOps | 1 step in the existing pipeline | None |
| dbt | Reads `manifest.json`, which dbt already writes | None (a file) |
| Terraform | Reads `terraform plan -json` in the same pipeline | None (a file) |
| Unity Catalog | Queries `information_schema` and system tables | 1 read-only service principal. Lineage system tables must be turned on by an account admin (a manual gap, rule 5) |
| Azure (later) | Azure Resource Graph | 1 read-only identity |

Only Unity Catalog needs a new credential in version 1.

### Workflow for the engineer

1. The engineer opens a pull request, as today.
2. The pipeline runs DataForge as 1 extra step.
3. DataForge writes a comment on the pull request. Example: "This change
   affects 3 tables owned by Finance. Owner: @finance-data."
4. A scheduled job checks Unity Catalog each night for schema changes on
   source tables, and alerts the downstream owners.

Nobody opens a new tool. The warning arrives where changes are already
reviewed.

### Deployment models

| Model | Where it runs | When |
|---|---|---|
| **In-pipeline (default)** | In the CI of the client, under the identity of the client | Version 1 |
| In-workspace | As a scheduled Databricks job in the workspace of the client | Phase 4 (source drift) |
| Hosted | On an OYS service | Only if design partners ask for it |

The default keeps all metadata and secrets inside the client environment. A
regulated company accepts this faster than a new external vendor.

### Setup cost

| Task | Effort | Who |
|---|---|---|
| Add the pipeline step | Hours | Platform engineer |
| Create and approve the read-only service principal | 1 day, plus approval time | Platform and security |
| Map each client setup (GitHub or Azure DevOps, 1 or many dbt projects) | 1 to 2 days | DataForge or OYS |
| **Tag owners on schemas, tables, and models** | **Weeks. Usually the largest task** | Client, with OYS help |

Owner tagging is not a tool problem. It is an organization problem, and it is
a natural OYS consulting service: DataForge shows the gaps, and OYS helps the
client close them.

### Streaming pipelines

Streaming tables in Unity Catalog have the same metadata as batch tables. A
schema change on a streaming source is found the same way. DataForge does not
watch the data flow. It watches structure and owners.

---

## 10. Status

| Area | State |
|---|---|
| Terraform for Azure Databricks and Unity Catalog | Merged (pull request 3). Passes `fmt` and `validate`. **Not applied** |
| Databricks backend with 2 identities | Code and offline tests. **Not run on a real workspace** |
| Graph builder, collectors, impact engine | **Not started** |
| Learning portal | **Stopped.** The live portal is still online until it is taken down |
| Desk research on boundary incidents | **Not started** |
| ADRs and threat model | Written for the first version. Need an update |
| Design partners | 0 |

---

## 11. Roadmap

Each phase ends with 1 published blueprint. A new phase starts only when the
blueprint of the current phase is published.

| Phase | Goal | Blueprint | Exit criterion |
|---|---|---|---|
| 1 | Reference platform live on Azure, with 3 teams: source, platform, analytics | Ownership boundaries on governed Databricks | Terraform applied. Each schema has an owner tag. Lineage system tables are on. The collector principal cannot read rows |
| 2 | Cross-layer graph with owners | One graph across Terraform, Unity Catalog, and dbt | The graph answers "who depends on this table" correctly for 10 test cases |
| 3 | Breaking-change check in CI | Catch breaking changes across team boundaries | PR comment names the right owners in 10 recorded scenarios |
| 4 | Source drift after the fact, plus incident tags | When the source changes under you | Alert within 1 run of a source schema change. Incident tags stored |
| 5 | Evidence of controlled change | Change evidence for regulated data platforms | Export that a DORA change process can use, reviewed by 1 compliance person |

After Phase 5: a field report on boundary incidents, with data from design
partners. This is the evidence that the research could not find.

### Next steps

1. **Validate the problem with desk research (2 weeks, parallel to Phase 1).**
   Collect public, dated incident cases and survey data, and map what existing
   tools cover. The method and the gate are in
   [research/method.md](research/method.md).
2. **Run Phase 1 on Azure.** The Terraform is ready.
3. **Archive the portal.** Fix nothing on learner sign-in.

---

## 12. Kill and pivot criteria

| Check | When | If it fails |
|---|---|---|
| Desk research passes all 3 gate checks in [research/method.md](research/method.md) | Week 2 | Stop the product. Keep DataForge as a portfolio project only |
| 2 design partners run the CLI on a real repository | Week 10 | Pivot to a consulting method (no software product) for OYS |
| DataForge finds something that dbt, Unity Catalog lineage, and existing PR tools do not | Phase 3 | Narrow to the gap, or stop |

---

## 13. Risks

1. **Crowded neighbors.** Datafold and Recce do impact analysis on dbt pull
   requests. dbt has model contracts. Gable and the Data Contract CLI work on
   contracts. Unity Catalog has lineage. The open question is whether
   *cross-layer plus owners* is a real gap. This is not yet checked. The desk
   research checks it before Phase 2 (gate check 3).
2. **The vendor may build it.** Databricks can add owner-aware impact to Unity
   Catalog. Mitigation: stay multi-layer (Terraform and dbt), where 1 vendor
   sees less.
3. **The problem size is uncertain.** About 24% of incidents is a vendor
   number. Rule 9 exists to produce better numbers.
4. **The costliest class is out of scope.** Changes in meaning are not visible
   in metadata. DataForge must not claim to solve them.
5. **Time.** A full-time job limits build speed. The narrow version 1 scope
   is the answer.
6. **Setup friction.** Without owner tags, DataForge tells the wrong people or
   nobody. If a client will not tag owners, the tool gives little value.
   Mitigation: version 1 also reports untagged assets as a gap list, so the
   first result is useful even before tagging is done.

---

## 14. History

| Date | Step |
|---|---|
| 10 Nov 2026 | Specification v1.0: an Azure-first academy with Databricks and 2 sandbox tiers |
| 10 Nov 2026 | LAB-001 end to end on DuckDB, with CI. Pull request 1 |
| 10 to 15 Nov 2026 | Databricks backend, token sign-in, Render deployment. Pull request 2 |
| 15 Nov 2026 | Platform proof track. Phase 1 started: Terraform and run isolation. Pull request 3 |
| 19 Nov 2026 | Redesign. Learning by building stopped. New direction: ownership-aware change impact across Terraform, Unity Catalog, and dbt |
| 19 Nov 2026 | Integration model added: runs inside client pipelines, read-only, owner tagging as the main setup task |
| 19 Nov 2026 | Pull request 3 merged: the Terraform becomes the reference platform. Interviews replaced by desk research |

---

## 15. Changes from the proposed version

The proposed version of 19 November 2026 had these differences:

1. **The verifier never reads rows.** The proposal said that the grader
   becomes a verifier that checks a contract "against the live table". The
   grader reads rows, which conflicts with rule 4. The verifier compares the
   contract with the table schema only.
2. **The research numbers wait for sources.** The numbers in section 2 have
   no source in the repository yet. They go in with the desk research.
3. **Rule 6 is reworded.** The new tool does not run SQL on DuckDB. The CI
   default is now offline tests with recorded metadata fixtures.
4. **Lineage system tables are a manual gap.** An account admin must turn them
   on. This is added to section 9 and to the Phase 1 exit criterion.
5. **Desk research replaces the interviews.** The research is done by Claude,
   with a written method and a gate of 3 checks. The kill criterion in section
   12 and the next steps in section 11 are changed to match.
