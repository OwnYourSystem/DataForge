# DataForge planning addendum: platform proof track

Date: 15 November 2026
Status: accepted, with 3 edits (see "Changes from the proposed version")

> **Replaced in part on 19 November 2026** by [../overview.md](../overview.md):
> the position, the goals, rules 3, 4 and 6, the new rule 9, and the roadmap.
> The phases below describe the learning portal and are no longer the plan.
Applies to: `OwnYourSystem/DataForge`
Read with: `docs/spec/dataforge-v1.0-original.md`, `docs/spec/fast-path.md`

---

## 1. Purpose

DataForge is a platform to build and learn best practices for data infrastructure. This addendum adds a second goal: DataForge must give public proof of principal-level platform engineering.

1 asset serves 3 goals:

| Goal | What DataForge must prove |
|---|---|
| Career | Platform engineering, Terraform, dbt, Databricks, Azure, AWS, CI/CD, observability, Data Mesh |
| Brand (OYS) | Authority through blueprints and ebooks |
| Mentoring | Ability to raise the skills of other engineers |

The flow of value is: **build, then lab, then blueprint, then ebook.** Each step uses the output of the step before it.

---

## 2. Positioning

Do not compete on "data engineering best practices" in general. Databricks Academy and dbt Learn are free.

DataForge position: **learn to build and own a governed data platform, end to end.**

The learner builds the controls and sees them work: identities, grants, contracts, cost limits and logs. Every lab, blueprint and chapter must show the governance and security reason for a design, not only the steps.

DataForge is a learning platform. It is not a regulated service, and it does not need a certification. Regulations are used only as examples of why companies ask for these controls. DORA (the EU regulation on IT risk in financial companies) is the main example.

---

## 3. Rules

These rules apply to all planning and all work in this track.

1. **Proof before publication.** Do not publish a blueprint or chapter about a feature until that feature runs live and the evidence is in the repo.
2. **1 milestone, 1 blueprint.** Each phase ends with 1 published blueprint. The ebook is the compiled blueprints. Do not write ebook text that has no blueprint behind it.
3. **Platform before product.** Platform work (infra, dbt standards, observability) comes before product features (UI polish, quotas, Tier B). Product features wait until real learners ask for them.
4. **Trusted and untrusted code stay apart.** Platform code lives outside `curriculum/`. Learner code never runs with platform credentials.
5. **Everything as code.** No manual setup in a cloud console. If a step is manual, document it as a gap and give it an issue.
6. **DuckDB stays the CI default.** Cloud runs are extra proof, not a requirement for every commit.
7. **Clean-room only.** No code, data, names, policies or network details from an employer. Use personal cloud accounts and synthetic or public data.
8. **Write down decisions.** Each important decision gets a short ADR in `docs/adr/`.

---

## 4. Target repository layout

Add these paths. Keep the existing layout.

```text
apps/                     existing: API, worker, web
curriculum/               existing: lessons (untrusted learner area)
infra/
  modules/
    databricks-workspace/
    unity-catalog/
    service-principals/
    sql-warehouse/
  envs/
    azure-dev/
    aws-dev/
platform/
  dbt/                    trusted platform dbt project (observability, contracts)
docs/
  adr/                    architecture decision records
  blueprints/             published blueprint sources
  threat-model.md
```

---

## 5. Phases

Each phase has a goal, tasks, acceptance criteria and 1 blueprint. A phase is done only when all acceptance criteria pass.

### Phase 1: Live Databricks on Azure, as code

**Goal:** The existing Databricks backend runs against a real Azure workspace. Terraform creates all the resources it needs.

**Tasks**

- [ ] Create `infra/modules/` for workspace, Unity Catalog catalog `dataforge_lab`, 2 service principals, grants and a serverless SQL warehouse.
- [ ] Create `infra/envs/azure-dev/` that uses the modules.
- [ ] Use remote Terraform state with locking.
- [ ] Replace the manual SQL steps in `docs/databricks.md` with Terraform.
- [ ] Run the live test in `docs/databricks.md` against the workspace.
- [ ] Add `terraform fmt`, `validate` and `plan` to CI on pull requests.
- [ ] Add a gated `apply` (manual approval) for the dev environment.
- [ ] Write ADR-001: why Terraform, state location, module boundaries.

**Acceptance criteria**

- `terraform apply` from an empty subscription gives a working environment.
- LAB-001 passes on Databricks, with the grade the same as on DuckDB.
- The run schema `df_run_<hex>` is dropped after each run. The sweep drops schemas that a stopped worker left.
- The service principals have least privilege. A test shows that the learner principal cannot read outside its run schema.
- `terraform destroy` removes everything. No cost after destroy.

**Blueprint 1:** Governed Databricks on Azure with Terraform and Unity Catalog.

### Phase 2: dbt standards and Data Mesh

**Goal:** dbt is part of how the platform is engineered, not only the subject of lessons. The platform shows Data Mesh patterns.

**Tasks**

- [ ] Create `platform/dbt/` as a trusted dbt project, separate from `curriculum/`.
- [ ] Define at least 2 domains (for example `sales` and `customers`) as dbt groups with owners.
- [ ] Use model `access` (`public`, `protected`, `private`) between domains.
- [ ] Add model contracts on all public models.
- [ ] Add model versions to 1 public model to show a safe breaking change.
- [ ] Map each domain to its own Unity Catalog schema or catalog, with grants for each domain owner.
- [ ] Add cross-project refs with the open-source `dbt-loom` plugin (dbt Core has no native cross-project ref). Write ADR-002 on this choice.
- [ ] Add slim CI: build only `state:modified+` on pull requests.
- [ ] Add 1 new lab that teaches contracts and access.

**Acceptance criteria**

- A change that breaks a public contract fails CI.
- A model in 1 domain cannot `ref()` a private model in another domain.
- Slim CI builds only changed models and their children.
- Domain grants in Unity Catalog match the dbt group owners.

**Blueprint 2:** Data Mesh with dbt contracts and Unity Catalog.

### Phase 3: AWS

**Goal:** The same platform runs on Databricks on AWS with the same modules where possible.

**Tasks**

- [ ] Add AWS versions of the modules, or make the modules cloud-neutral with a provider switch.
- [ ] Create `infra/envs/aws-dev/`.
- [ ] Run LAB-001 and the Phase 2 dbt project on AWS.
- [ ] Write ADR-003: what is shared between clouds and what is not.

**Acceptance criteria**

- The same lesson and the same dbt project pass on Azure and AWS.
- Cloud-specific code is limited to the `envs/` and provider layers.
- A table in the blueprint shows the differences between the 2 clouds.

**Blueprint 3:** One governed platform, 2 clouds.

### Phase 4: Observability and reliability

**Goal:** The platform measures its own cost, speed and failures. The measurements are built with dbt.

**Tasks**

- [ ] In `platform/dbt/`, build models on Databricks system tables for warehouse cost, query duration and failed runs.
- [ ] Add models on the `executions` table for run duration, pass rate and queue wait.
- [ ] Define 3 service level objectives, for example: 95% of runs finish in under 60 seconds.
- [ ] Add alerts for SLO breaches and for cost above a monthly limit.
- [ ] Add a simple dashboard.

**Acceptance criteria**

- Cost for each lesson run is visible.
- An SLO breach sends an alert in a test.
- The observability models follow the same contracts and standards as Phase 2.

**Blueprint 4:** Platform cost and reliability with dbt and system tables.

### Phase 5: Compile the ebook

**Goal:** 1 ebook from blueprints 1 to 4.

**Tasks**

- [ ] Edit the 4 blueprints into chapters.
- [ ] Add 1 chapter on governance across the platform: which control answers which risk. Use DORA as an example of why companies ask for these controls.
- [ ] Add 1 chapter on the threat model.

**Acceptance criteria**

- Every chapter links to code and evidence in the repo.
- No chapter describes a feature that does not run.

---

## 6. Cross-cutting work

Do these along with the phases.

| Item | When | Output |
|---|---|---|
| Threat model | Phase 1, update each phase | `docs/threat-model.md` |
| README rewrite | After Phase 1 | Lead with platform architecture, then lessons |
| Architecture diagram | After Phase 1, update each phase | 1 diagram in README |
| Cost log | Every phase | Cost of each phase in each blueprint |
| Talks | After Phase 2 | 1 meetup talk from a blueprint |

---

## 7. Out of scope for this track

These stay parked until a phase is done and real learners ask for them:

- Tier B (Terraform labs for learners)
- Monthly quotas
- SSE log streaming
- UI redesign
- Payment and paid plans

Alembic migrations are an exception. Add them before the first schema change, because the platform needs them.

---

## 8. Capacity and order

Budget: about 20 hours each week for all OYS work.

- DataForge is the main project while this track runs.
- Pause at least 1 other project until Phase 1 ships.
- Estimated pace: about 3 to 6 weekends per phase. Phase 1 is the largest, because it creates the base for all other phases.
- Do not start a new phase until the blueprint of the current phase is published.

---

## 9. Definition of done for the track

The track is done when:

1. Phases 1 to 4 pass all acceptance criteria.
2. 4 blueprints are published.
3. The ebook is compiled.
4. The README shows the platform architecture first.
5. All infrastructure can be created and destroyed from code on Azure and AWS.

---

## 10. Risks

| Risk | Effect | Control |
|---|---|---|
| Product work takes the hours | Gaps stay open | Rule 3. Park product features. |
| Publishing before proof | Loss of credibility | Rule 1. Evidence in the repo first. |
| Cloud cost grows | Money lost | Serverless warehouse, short auto-stop, `destroy` after tests, cost alerts |
| Employer IP conflict | Legal risk | Rule 7. Check the employment contract. |
| Scope grows across other projects | No phase finishes | Section 8. Pause other projects. |
| Generic content | No audience | Section 2. The governance reason for each design in every output. |

---

## Changes from the proposed version

The proposed version of 15 November 2026 had these 3 differences:

1. **ISO/IEC 42001 is removed** from section 2 and from Phase 5. It is a standard for AI management systems, and DataForge has no AI workload, so there is nothing to map.
2. **The position is changed** from "best practices for governed data platforms in regulated environments" to "learn to build and own a governed data platform, end to end".
3. **DORA stays only as an example** of why companies ask for these controls. It is not a requirement for the code.

The risk row "Generic content" in section 10 is changed to agree with the new position.
