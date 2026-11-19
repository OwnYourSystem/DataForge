# DataForge

**Learn to build and own a governed data platform, end to end.**

Status on 19 November 2026. This page is the short description of the whole
project: what it is, where it goes, and what is true today.

---

## 1. What DataForge is

DataForge is a web portal for hands-on data engineering labs. A learner gets a
real task, writes the code in the browser, and runs it. An independent grader
then checks the result that the code made, not only that the code ran.

DataForge is also a platform that is built in the open. The platform itself is
the second product: each part is built as code, documented, and then
published as a blueprint.

---

## 2. The problem

Most online training for data engineering gives videos, quizzes, and
notebooks where the code is already written. A learner can finish a course and
still not be able to do the work. The solution is often one click away, and
"completed" means "ran all the cells".

Training from a vendor also teaches the products of that vendor. It seldom
shows the controls that a company needs around a data platform: identities,
access rules, data contracts, cost limits, and logs.

---

## 3. The position

DataForge does not compete on general "data engineering best practices".
Databricks Academy and dbt Learn are free.

The position is: **learn to build and own a governed data platform, end to
end.** The learner builds the controls and sees them work. Every lab,
blueprint, and chapter shows the governance and security reason for a design,
not only the steps.

DataForge is a learning platform. It is not a regulated service, and it does
not need a certification. Regulations such as DORA (the EU regulation on IT
risk in financial companies) are used only as examples of why companies ask
for these controls.

---

## 4. Goals

DataForge has 2 goals.

### Goal 1: a learning platform

A learner must be able to:

1. Sign in and open a lab, with no local setup.
2. Write code in an online editor.
3. Run it through an approved operation, not a free shell.
4. Get an independent grade with a clear list of what passed and what failed.
5. Stop, and continue later with the work saved.

### Goal 2: public proof of platform engineering

The same build serves 3 aims:

| Aim | What DataForge must prove |
|---|---|
| Career | Platform engineering, Terraform, dbt, Databricks, Azure, AWS, CI/CD, observability, Data Mesh |
| Brand (OwnYourSystem) | Authority through blueprints and an ebook |
| Mentoring | The ability to raise the skills of other engineers |

The flow of value is: **build, then lab, then blueprint, then ebook.** Each step
uses the output of the step before it.

---

## 5. Rules

These rules apply to all work. The full text is in
[spec/platform-proof-track.md](spec/platform-proof-track.md).

1. **Proof before publication.** No blueprint, chapter, or flyer describes a
   feature that does not run live, with the evidence in the repository.
2. **1 milestone, 1 blueprint.** Each phase ends with 1 published blueprint.
3. **Platform before product.** Platform work comes before product features.
   Product features wait until real learners ask for them.
4. **Trusted and untrusted code stay apart.** Learner code never runs with
   platform credentials.
5. **Everything as code.** A manual step is written down as a gap.
6. **DuckDB stays the CI default.** Cloud runs are extra proof.
7. **Clean-room only.** No code, data, or names from an employer.
8. **Write down decisions** as ADRs in [adr/](adr/).

---

## 6. What a learner can do today

1. Sign in with a code from an email. There is no password.
2. Open LAB-001: clean 5 customer records with a dbt staging model.
3. Write the SQL in the editor. The work is saved.
4. Select **Build and test**. The platform runs dbt and the data tests.
5. Get a score out of 100 from 5 checks. A pass needs 80 or more, with the
   2 critical checks passed.
6. Come back later. The code and the best score are still there.

The solution is never shown. A learner can run only their own model, and only
through the approved operation.

---

## 7. How it is built

```text
Browser (Next.js, Monaco editor)
  └── Web server: forwards /api to the API
        └── API (FastAPI): identity, lessons, files, run requests
              └── Postgres: state and the job queue
                    └── Worker: runs dbt, grades, cleans up
                          └── SQL engine: DuckDB (default) or Azure Databricks
```

| Part | Technology |
|---|---|
| Web portal | Next.js, TypeScript, Monaco editor |
| API | Python, FastAPI |
| Worker | Python, dbt |
| Database | Postgres |
| Sign-in | Supabase Auth (email code). The API checks signed tokens |
| SQL engines | DuckDB, Azure Databricks with Unity Catalog |
| Infrastructure | Terraform: workspace, catalog, identities, SQL warehouse |
| Delivery | GitHub Actions, Docker, Render |

### Security model

- The learner sends an operation id, never a command.
- The learner can change 1 file. All other dbt files are trusted.
- A SQL guard permits 1 `select` that reads only `source()` and `ref()`.
- On Databricks, the learner identity has rights on the schema of its own run
  only. A separate, trusted identity does all other work.
- Each dbt step gets only its own credential.
- The grader reads the real table and calculates the expected values itself.

The full list of threats, controls, and gaps is in
[threat-model.md](threat-model.md).

---

## 8. Status

| Area | State |
|---|---|
| LAB-001 on DuckDB, end to end | Works. Tested in CI on each push |
| Independent grading | Works |
| Saved work and best score | Works |
| Portal on Render (free single container) | Live at dataforge-ayum.onrender.com |
| Sign-in on the live portal | **Not working.** 3 settings in the Supabase project are open |
| Databricks backend with 2 identities | Code and offline tests. **Not run on a real workspace** |
| Terraform for Azure | Passes `fmt` and `validate`. **Not applied** |
| ADRs and threat model | Written: ADR-001, ADR-004, threat model |
| Explore, build, prove lab format | Mock-up only |
| Labs | 1 |

---

## 9. Roadmap

Each phase ends with 1 published blueprint. A new phase starts only when the
blueprint of the current phase is published.

| Phase | Goal | Blueprint | State |
|---|---|---|---|
| 1 | Live Databricks on Azure, as code | Governed Databricks on Azure with Terraform and Unity Catalog | In progress: code written, waits for an Azure run |
| 2 | dbt standards and Data Mesh: contracts, access, domains | Data Mesh with dbt contracts and Unity Catalog | Not started |
| 3 | The same platform on AWS | One governed platform, 2 clouds | Not started |
| 4 | Cost, speed, and failures measured with dbt | Platform cost and reliability with dbt and system tables | Not started |
| 5 | The ebook, from blueprints 1 to 4 | | Not started |

### Next steps

1. **Run Phase 1 on Azure.** Follow [../infra/README.md](../infra/README.md),
   then the Databricks live test.
2. **Fix sign-in on the live portal.** Set the 3 Supabase settings in
   [auth.md](auth.md).
3. **Merge Phase 1** when its acceptance criteria pass.

---

## 10. Out of scope for now

These wait until a phase is done and real learners ask for them:

- Terraform labs for learners (Tier B)
- Monthly quotas and paid plans
- Live log streaming
- A UI redesign

---

## 11. History

| Date | Step |
|---|---|
| 10 Nov 2026 | Specification v1.0: an Azure-first academy with Databricks and 2 sandbox tiers |
| 10 Nov 2026 | Fast path: LAB-001 end to end on DuckDB, with CI. Pull request 1 |
| 10 to 15 Nov 2026 | Databricks backend, token sign-in, Render deployment. Pull request 2 |
| 15 Nov 2026 | Platform proof track accepted. The position changed to building and owning a governed platform |
| 15 Nov 2026 | Phase 1 started: Terraform and run isolation. Pull request 3 |

---

## 12. Documents

| Document | Contents |
|---|---|
| [spec/dataforge-v1.0-original.md](spec/dataforge-v1.0-original.md) | The first specification |
| [spec/fast-path.md](spec/fast-path.md) | Decisions that changed it |
| [spec/platform-proof-track.md](spec/platform-proof-track.md) | The plan from here |
| [adr/](adr/) | Architecture decisions |
| [threat-model.md](threat-model.md) | Threats, controls, and gaps |
| [databricks.md](databricks.md) | The Databricks backend |
| [auth.md](auth.md) | Sign-in |
| [deploy.md](deploy.md) | The Render deployment |
| [../infra/README.md](../infra/README.md) | Terraform and the Azure steps |
| [marketing/](marketing/) | The flyer and its brief |
