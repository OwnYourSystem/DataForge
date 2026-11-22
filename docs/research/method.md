# Desk research: method and gate

Date: 19 November 2026
Status: method accepted. Research not started.
Done by: Claude (desk research). There are no interviews.

## Question

Do changes that cross an ownership boundary often cause data incidents, and
do the tools that teams already have miss them?

## What is collected

| Part | Sources |
|---|---|
| Incident cases | Public postmortems and engineering blogs; GitHub issues in dbt, Unity Catalog, and Terraform provider projects; public community threads (dbt Discourse, r/dataengineering) |
| Survey data | Industry surveys on data incidents and ownership. The publisher of each survey is named, and vendor surveys are marked |
| Tool landscape | Documentation of dbt contracts, Unity Catalog lineage, Datafold, Recce, Gable, Data Contract CLI, and similar tools |

## Evidence log: 1 row for each case

| Field | Values |
|---|---|
| Source | Link |
| Date | Date of the incident, or of the publication |
| Source type | Independent, or vendor |
| Layer that changed | Source schema, Terraform or grants, dbt model, or meaning |
| Crossed a team boundary | Yes, no, or not known |
| How it was found | For example: a failed job, a wrong report, a user |
| Time to find | As published, or not known |
| Caught by a tool the team had | Yes, no, or not known |
| Would DataForge version 1 catch it | Yes, no, or partly, with the reason |

## Gate

The product continues to Phase 2 only if all 3 checks pass:

1. **At least 15 independent, dated public cases** from the last 3 years in
   which a structural change crossed a team boundary and broke data
   downstream. Vendor marketing does not count.
2. **In at least 1 case out of 3,** the tools that the team already had did
   not catch the problem.
3. **The tool landscape shows a real gap:** at least 1 layer combination,
   with owners, that no listed tool covers.

If a check fails, DataForge stays a portfolio project
([../overview.md](../overview.md), section 12).

## Limits

- **Public cases are biased.** They come mostly from large companies and from
  vendors, and most incidents are never published. A count of public cases is
  a lower bound, not a rate.
- **Private details cannot be checked,** and there is no follow-up question.
- **Desk research does not replace design partners.** The second kill
  criterion (2 design partners run the CLI by week 10) and rule 3 still need
  real people.

## Deliverables

| File | Contents |
|---|---|
| `boundary-incidents.md` | The evidence log, the findings, and a pass or fail for each gate check |
| `tool-landscape.md` | A gap table: what each tool covers, by layer and by owner |
| Sources for section 2 of the overview | The surveys behind the numbers 39% to 51% and about 24% |
