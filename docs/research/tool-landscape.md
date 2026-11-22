# DataForge: tool landscape and gap table

> **Review note (22 November 2026).** Written by a research agent and reviewed
> by Claude. Every row comes from search result text, because this research
> session could not open the source pages. Read the page before you quote a
> row in public (rule 1). Overview: [boundary-incidents.md](boundary-incidents.md).


Research date: 2026-11-22.
Question: does any existing tool flag, on a Terraform PR before merge, which downstream owners will break across Terraform, Azure, Unity Catalog and dbt?

## How this was checked

- I used web search only. WebFetch was blocked in this sandbox for docs.atlan.com, docs.getdbt.com and learn.microsoft.com (DNS not allowed). I stopped trying other hosts after that.
- So every row below is "search snippet only". No page was read in full.
- Search snippets are summaries of the page. They can be wrong or old. Treat each claim as "needs a page read before we quote it in a pitch".
- Vendor blog and marketing claims are marked as such.
- "Not confirmed" means I found no source either way. It does not mean the feature is missing.

## Short answer

- No tool I found reads Terraform (or Azure resource config) AND Unity Catalog AND dbt in one graph.
- No tool I found starts from a Terraform PR and names downstream data owners.
- Many tools do the dbt half well: dbt PR to downstream models, dashboards and sometimes owners.
- Terraform PR tools (Atlantis, Spacelift, env0, HCP Terraform, Infracost, Checkov) only know infrastructure. None of them, per the sources, knows about downstream data consumers.
- Verdict on the gate question: **pass, with medium confidence**. Details at the end.

## Gap table

Legend for layers: TF = Terraform, AZ = Azure resources, UC = Unity Catalog, dbt = dbt, BI = BI tools, Code = app or Spark code.

| Tool | Layers it reads | Knows owners? | Before merge (PR) or after (runtime)? | Detects structural breaking changes? | Notifies affected downstream owners? | Reads data rows? | OSS / commercial | Source URL(s) | Verified from |
|---|---|---|---|---|---|---|---|---|---|
| dbt model contracts + versions (dbt Core) | dbt | Partly. Groups have an owner (name or email). meta.owner is free-form | PR (with state:modified in CI) | Yes. Contract checks under state:modified error on breaking changes such as a removed column. Some reported edge cases (issues 8028, 8030) | No | No for the contract check | OSS | https://docs.getdbt.com/docs/mesh/govern/model-contracts ; https://github.com/dbt-labs/dbt-core/issues/8384 ; https://github.com/dbt-labs/dbt-core/issues/8030 | Search snippet only |
| dbt state:modified + defer (Slim CI) | dbt | No | PR | Only picks changed nodes and their children. Not column-level by itself | No | Yes if you run `dbt build` (it builds models). Selection itself does not | OSS | https://docs.getdbt.com/reference/node-selection/defer ; https://docs.getdbt.com/reference/node-selection/state-comparison-caveats | Search snippet only |
| dbt platform Advanced CI (compare changes) | dbt (warehouse output) | No for the compare | PR. Posts a summary as a Git comment | Yes, data-level: column type, order, value and key changes | No | Yes (compares data) | Commercial, Enterprise tier | https://docs.getdbt.com/docs/deploy/advanced-ci ; https://getdbt.com/blog/announcing-advanced-ci | Search snippet only |
| dbt Catalog (Explorer) column lineage + Mesh cross-project | dbt (multi-project) | Partly. Exposure owners and group owners via Discovery API | Neither as a gate. It is a browse UI | No | No | No | Commercial, Enterprise tier | https://docs.getdbt.com/docs/explore/column-level-lineage ; https://docs.getdbt.com/docs/explore/dbt-explorer-faqs ; https://docs.getdbt.com/docs/explore/explore-multiple-projects | Search snippet only. Sources disagree on cross-project column lineage |
| dbt model notifications | dbt | Yes. Group owner email | After (job run) | No | Yes, on job run status, not on PR impact | No | Commercial (dbt platform) | https://docs.getdbt.com/docs/deploy/model-notifications | Search snippet only |
| Unity Catalog lineage system tables (system.access.table_lineage, column_lineage) | UC (plus notebooks, jobs, dashboards, SQL) | Owner is a separate field (information_schema.tables.table_owner). Not in lineage rows | After. Lineage is captured from runs | No | No | No (metadata only) | Commercial (Databricks) | https://docs.databricks.com/aws/en/admin/system-tables/lineage ; https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage.html ; https://learn.microsoft.com/azure/databricks/sql/language-manual/information-schema/tables | Search snippet only |
| Unity Catalog tags and governed tags | UC | Partly. Tags can hold an owner key. table_owner exists | n/a (metadata store) | No | No | No | Commercial (Databricks) | https://docs.databricks.com/aws/en/database-objects/tags ; https://docs.databricks.com/aws/en/admin/system-tables/governed-tags | Search snippet only |
| Databricks data quality monitoring (anomaly detection + data profiling, ex Lakehouse Monitoring) | UC tables | Not confirmed | After (runtime) | No (freshness, completeness, stats) | Not confirmed | Yes (profiles data) | Commercial (Databricks) | https://docs.databricks.com/aws/en/lakehouse-monitoring/data-quality-monitoring ; https://docs.databricks.com/aws/en/lakehouse-monitoring/anomaly-detection | Search snippet only |
| Datafold | dbt, warehouse, BI (for example Power BI) | Not confirmed | PR | Yes. Schema and data diff plus column-level lineage | Not confirmed (PR comment, not owner routing) | Yes (data diff) | Commercial | https://datafold.com/blog/dbt-lineage ; https://datafold.com/blog/announcing-power-bi-integration ; https://datafold.com/integrations/dbt-core | Search snippet only. Mostly vendor pages |
| Recce | dbt, warehouse | Not confirmed | PR (validation checks in PR comment) | Partly. "Breaking change" visual cues and column-level lineage. Logic not confirmed from docs | Not confirmed | Yes (profile diff, query diff) | OSS core + commercial cloud | https://github.com/DataRecce/recce ; https://pypi.org/project/recce/1.46.2/ ; https://medium.com/inthepipeline/hands-on-data-impact-analysis-with-recce-80ea4156c6ec | Search snippet only |
| Gable | App code (static analysis), data contracts | Yes, per vendor. PR Impact Map "suggests code owners as reviewers". Can tag subscribed consumers | PR | Yes, against contracts | Yes, per vendor (comment on PR, tag subscribed consumers) | Not confirmed (static code analysis suggests no) | Commercial | https://www.gable.ai/blog/how-gable-implements-data-contracts---and-stops-bad-things-from-happening ; https://dataproducts.substack.com/p/tackling-datas-biggest-culture-problem ; https://docs.gable.ai/docs/data_contracts/what_are_data_contracts | Search snippet only. Marketing. No Terraform support found |
| Data Contract CLI (datacontract.com) | Contract files (DCS or ODCS); can test against data sources | Only what the contract file says | PR possible (CLI in CI) | Yes. `datacontract breaking` compares 2 contract versions, exit 1 on ERROR | No | Yes for `test`. No for `breaking`/`changelog` | OSS | https://docs.datacontract.com/compare-contract-versions ; https://docs.datacontract.com/release-notes ; https://github.com/datacontract/datacontract-cli/releases | Search snippet only |
| Open Data Contract Standard (ODCS, Bitol) | Spec only (no runtime) | Yes as a field. v3.1.0 makes the owning team a first-class property | n/a (a standard) | n/a | n/a | n/a | Open standard (Linux Foundation) | https://bitol-io.github.io/open-data-contract-standard/latest/home ; https://bitol-io.github.io/open-data-contract-standard/latest/changelog | Search snippet only |
| terraform plan | TF (and the Azure/Databricks resources it manages) | No | PR (when run in CI) | Shows resource changes. Does not show effective data access or data consumers | No | No | OSS / BSL (HashiCorp) | (no single page read; behaviour described in https://adamtheautomator.com/databricks-unity-catalog-terraform/) | Search snippet only |
| Atlantis | TF | No | PR. Posts plan as comment. Conftest (OPA) policy checks on plan | Only what your Rego policy encodes | No | No | OSS | https://www.runatlantis.io/docs/policy-checking | Search snippet only |
| Spacelift (OPA) | TF and other IaC | No | PR / plan gate | Only what your Rego policy encodes | No | No | Commercial | https://docs.spacelift.io/concepts/policy ; https://spacelift.io/blog/open-policy-agent-opa-terraform | Search snippet only |
| env0 (OPA) | TF | No | Plan / deploy gate (for example cost approval) | Only what your policy encodes | No | No | Commercial | https://www.env0.com/blog/how-policy-as-code-enhances-infrastructure-governance-with-open-policy-agent-opa | Search snippet only |
| HCP Terraform / Terraform Enterprise (Sentinel) | TF config, state, plan | No | Run / plan gate | Only what your Sentinel policy encodes | No | No | Commercial | https://www.hashicorp.com/ar/products/terraform/use-cases/enforce-policy-as-code | Search snippet only |
| Infracost | TF | No | PR comment with cost diff | No (cost only) | No | No | OSS CLI + commercial app | https://github.com/infracost/actions | Search snippet only |
| Checkov / tfsec | TF | No | PR / pre-commit | Misconfig and security rules. Databricks-specific Checkov rules not confirmed | No | No | OSS (Checkov by Prisma Cloud) | https://handbook.sourcegraph.com/departments/security/tooling/checkov | Search snippet only |
| reachdiff (found once, unconfirmed) | TF plan JSON | No | PR. "Effective-access diff" with exit code | Access changes, not data breakage | No | No | Not confirmed | https://dev.to/reachdiff/who-gains-access-when-this-terraform-plan-is-applied-237c | Search snippet only. A second search found nothing else on it |
| Atlan | Many connectors incl. dbt, Databricks/UC, BI | Yes in catalog. Whether the PR comment names owners: not confirmed | PR (GitHub/GitLab action on dbt model changes). Contract impact analysis in GitHub is Private Preview | Lists impacted downstream assets (capped at 100) | Not confirmed | No (metadata) | Commercial | https://docs.atlan.com/apps/connectors/etl-tools/dbt/how-tos/add-impact-analysis-in-github ; https://docs.atlan.com/product/capabilities/governance/contracts/how-tos/add-contract-impact-analysis-in-github ; https://shipped.atlan.com/new-integration-with-github-2MTDKU | Search snippet only |
| Collibra | Many connectors, automated lineage | Yes (catalog) | After / in catalog. A third-party site claims data contracts with PR checks (GA March 2026), not confirmed | Impact view of change effects | Not confirmed | No (metadata) | Commercial | https://collibra.com/blog/impact-analysis-simplified-by-automated-lineage ; https://www.modern-datatools.com/compare/collibra-vs-foundational | Search snippet only |
| Alation | Many connectors | Yes (catalog) | After. Impact analysis reports exported as CSV | No | Manual (Alation blog says engineer sees "which stakeholders need to be notified") | No | Commercial | https://docs.alation.com/en/latest/analyst/Lineage/LineageImpactAnalysis.html ; https://alation.com/blog/alation-manta-automate-advanced-data-lineage | Search snippet only |
| DataHub | 150+ sources incl. dbt, Databricks | Yes (catalog owners) | Both possible. Impact analysis via UI and GraphQL. A dbt GitHub action (datahub-dbt-impact-action) is mentioned; status not confirmed | Lineage impact only | Not out of the box. Community actions (ContextCI) can @-mention DataHub owners | No | OSS core (Apache 2.0) + commercial cloud | https://docs.datahub.com/docs/act-on-metadata/impact-analysis ; https://support.datahub.com/hc/en-us/articles/42653605290907-GitHub-Actions-Framework-for-Impact-Analysis ; https://devpost.com/software/contextci | Search snippet only |
| OpenMetadata | Many connectors incl. dbt, Databricks/UC | Yes | After. Fires on metadata change events (for example schema change) | Detects schema changes after they happen | Yes. "Notify Downstream" walks lineage and alerts downstream owners | No for lineage. Profiler can read data | OSS (Apache 2.0 core) + Collate commercial | https://docs.open-metadata.org/v2.0.x/how-to-guides/data-quality-observability/alerts-notifications/notify-downstream | Search snippet only |
| Microsoft Purview (Unified Catalog) | Azure sources, Databricks UC (lineage via UC system tables) | Yes (owners in catalog). Known issue: owner updates do not always flow to data products | After (scan based) | No | Data quality alerts to stewards. Schema-change owner alerts not confirmed | Data quality scans read data. Lineage does not | Commercial | https://learn.microsoft.com/purview/concept-data-lineage ; https://techcommunity.microsoft.com/blog/microsoft-security-blog/introducing-lineage-tracking-for-azure-databricks-unity-catalog-in-microsoft-pur/4279185 ; https://learn.microsoft.com/en-us/purview/how-to-data-quality-notifications ; https://learn.microsoft.com/purview/data-governance-known-issues | Search snippet only |
| Monte Carlo | Warehouse/lakehouse (incl. Databricks), dbt, BI | Yes (observability owners) | Mostly after. GitHub integration runs a lineage check on PR (needs dbt). Circuit breakers are runtime | Mostly data anomalies; links PRs to incidents after the fact | Runtime alerts. PR owner routing not confirmed | Yes (monitors) | Commercial | https://montecarlodata.com/github-integration ; https://montecarlodata.com/blog-monte-carlo-first-to-detect-breaking-code-changes-with-new-databricks-gitlab-integrations | Search snippet only. 2023/2024 posts |
| Bigeye | Warehouse, lineage | Not confirmed | After (runtime). No PR workflow found | No | Not confirmed | Yes | Commercial | https://www.bigeye.com/blog/using-bigeye-data-lineage-for-actionable-root-cause-and-impact-analysis | Search snippet only |
| Sifflet | dbt, warehouse, BI | Not confirmed in the PR report | PR (GitHub action, GitLab component "Sifflet Impact Report") plus runtime monitors | Lists downstream assets; not structural classification | Not confirmed | Yes for monitors | Commercial | https://docs.siffletdata.com/docs/dbt-impact-analysis-github-action ; https://docs.siffletdata.com/docs/dbt-impact-analysis-gitlab-component | Search snippet only |
| Elementary | dbt | Yes for runtime alerts (owner tags, routing) | PR comment (test history, incidents, downstream impact, merge risk) plus runtime | Partly (merge risk, not contract-level) | Runtime alerts yes. PR-time owner alerts not confirmed | Yes for tests/monitors | OSS + commercial cloud | https://docs.elementary-data.com/cloud/features/ci | Search snippet only |
| Soda | Data sources via contracts | Not confirmed | Both. Vendor guide shows a PR gate for schema contract checks | Yes (schema checks against contract) | Not confirmed | Yes (runs checks on data) | OSS core + commercial cloud | https://soda.io/blog/enforce-data-contracts-ci-cd-pipelines | Search snippet only. Vendor blog |
| SQLMesh / Tobiko | SQLMesh models | No | Before apply (plan) | Yes. Classifies breaking, non-breaking, forward-only, indirect, metadata, using column-level lineage | No | Not for classification | OSS + commercial (Tobiko Cloud) | https://sqlmesh.readthedocs.io/en/stable/concepts/plans/ ; https://tobikodata.com/blog/automatically-detecting-breaking-changes-in-sql-queries | Search snippet only |
| Foundational | Code (dbt, Spark, SQL), warehouses, orchestration, BI | Yes, per third parties ("suggested owners" in PR post) | PR. Can block merge | Yes, per third parties | Partly. Lists suggested owners in PR | No (code analysis) | Commercial | https://www.foundational.io/platform/data-lineage-platform ; https://www.modern-datatools.com/compare/collibra-vs-foundational ; https://www.g2.com/products/foundational/discuss | Search snippet only. Mostly third-party summaries. Terraform and Databricks UC not confirmed |
| Datadog Data Observability CI/CD | dbt, warehouse (incl. Databricks), OpenLineage | Partly ("route review to owners" per search summary) | PR | Data drift checks plus impact lineage | Not confirmed | Yes (drift needs read access, GRANT SELECT) | Commercial | https://docs.datadoghq.com/data_observability/cicd/ | Search snippet only |
| Metaplane | dbt, warehouse, BI | Not confirmed | PR comment with downstream impact | Column lineage impact | Not confirmed | Yes for monitors | Commercial | https://www.metaplane.dev/blog/announcing-impact-analysis-in-dbt-pull-requests | Search snippet only |
| Small OSS dbt CI tools (whatbreaks, parrant, dbt-guard, Paradime lineage diff) | dbt only | No (parrant shows exposures) | PR | Yes, column-level (whatbreaks, dbt-guard) | No | No (whatbreaks says no warehouse needed) | OSS (Paradime commercial) | https://pypi.org/project/whatbreaks/ ; https://pypi.org/project/parrant/ ; https://pypi.org/project/dbt-guard/ ; https://docs.paradime.io/app-help/documentation/bolt/ci-cd/lineage-diff | Search snippet only |

## Gate question

"Is there at least 1 layer combination, with owners, that no listed tool covers?"

### Case examined

A Terraform PR changes a Unity Catalog grant (for example `databricks_grants` on a catalog or schema) or a storage resource (for example an Azure storage account or external location). That object backs a UC table. A dbt model reads that table. A downstream team owns the model or its exposure. We want that team named on the Terraform PR, before merge.

### Layer by layer

1. **Terraform PR tools** (terraform plan, Atlantis, Spacelift, env0, HCP Terraform, Infracost, Checkov). They see the resource diff. None of the sources says any of them knows about data lineage or data owners. Policy engines (OPA, Sentinel) can only check what you feed them. You could write a Rego policy that loads an external lineage file. That is custom engineering, not a product feature. This is the closest "with configuration" path, and it would basically be building DataForge inside a policy engine.
2. **Unity Catalog**. Has lineage tables and owner fields, but records lineage after runs. It has no idea of a pending Terraform change.
3. **dbt PR tools** (Datafold, Recce, dbt Advanced CI, Sifflet, Elementary, Metaplane, Datadog, Atlan action, small OSS tools). All trigger on dbt file changes. None was found that triggers on a Terraform file change.
4. **Catalogs** (Atlan, DataHub, OpenMetadata, Purview, Collibra, Alation). They hold owners and cross-system lineage. None was found with a Terraform or Azure-config connector that maps a pending IaC change to data assets. A search for Terraform-state ingestion into these catalogs found nothing. With custom code (read plan JSON, map resource IDs to catalog URNs, call lineage API, post a PR comment) DataHub or OpenMetadata could do it. That is a build, not a feature.
5. **Code-level contract tools** (Gable, Foundational). Closest in spirit: PR time, code-based, owners. But their sources talk about application code, dbt, Spark, SQL and BI. No Terraform or grant/storage coverage was found.

### Closest competitor for each gap

| Gap | Closest competitor | What it lacks |
|---|---|---|
| Terraform grant or storage change -> UC object -> dbt -> owner, on the TF PR | Atlantis or Spacelift with a custom OPA policy | No lineage, no owners. You must build and feed the graph yourself |
| Same chain, but owner notification | OpenMetadata "Notify Downstream" | Fires after the change lands (metadata event), not on the PR. No Terraform input |
| Same chain, PR-time cross-system impact with owners | Foundational (third-party claims) and Gable (vendor claims) | No confirmed Terraform, Azure or UC grant/storage layer |
| Same chain, catalog-driven PR comment | Atlan GitHub action | Triggers on dbt model changes only. Owner names in comment not confirmed |
| UC grant change -> who loses access | reachdiff (unconfirmed) | Access diff only. No data lineage, no dbt, no owners |
| dbt -> downstream owner on PR | Datafold, Elementary, Datadog, Sifflet | dbt-only trigger. Reads data rows for diffs (DataForge does not) |

### Verdict: PASS (medium confidence)

Reasons:
- No source showed any tool that takes a Terraform PR as input and names downstream data owners across UC and dbt.
- Terraform tools lack data context. Data tools lack a Terraform trigger. Catalogs have owners and lineage but act after the fact or on dbt changes only.
- The gap can be closed by heavy custom work on DataHub, OpenMetadata or an OPA policy setup. That is a real substitute DataForge will compete with ("we built it ourselves").

Why only medium confidence:
- All evidence is from search snippets. No full page was read.
- Foundational and Gable could have Terraform support not shown in search results. Ask for a demo or check their docs directly.
- Atlan and Collibra ship fast. Their "data contracts in PR" features (Atlan Private Preview, Collibra claimed GA March 2026) should be re-checked.

## Problems hit

- WebFetch was blocked for docs.atlan.com, docs.getdbt.com and learn.microsoft.com. Every row is "search snippet only".
- Recce official docs (docs.reccehq.com) did not show up in search. Its breaking-change logic is not confirmed.
- Foundational's own site did not show up in a site-restricted search. Its rows rely on G2 and Modern Data Tools summaries.
- Bigeye: no PR workflow found at all.
- reachdiff showed up once (dev.to post) and could not be confirmed by a second search.
- dbt Catalog cross-project column lineage: the FAQ and the quickstart disagree.
- Several Monte Carlo sources are from 2023 and 2024. Current state not confirmed.

## Next steps to raise confidence

1. Allow docs.getdbt.com, docs.databricks.com, learn.microsoft.com, docs.atlan.com, docs.datahub.com, docs.open-metadata.org, foundational.io, gable.ai in the sandbox network, then re-read the key pages.
2. Ask Foundational and Gable directly: "Do you parse Terraform? Do you map databricks_grants or azurerm storage changes to downstream tables?"
3. Check if any DataHub or OpenMetadata community connector ingests Terraform state.
