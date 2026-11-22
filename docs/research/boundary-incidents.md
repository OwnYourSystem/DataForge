# Boundary incidents: evidence log and gate result

Date: 22 November 2026
Done by: Claude (desk research, with 3 research agents and 1 review pass)
Method: [method.md](method.md)

## Result in 1 paragraph

**Check 1 fails by 1 case: 14 strict cases of the 15 needed. Checks 2 and 3
pass.** Round 1 (22 November) found 11 strict cases. Round 2 (22 November)
added 3, and 2 of those are borderline (see [Round 2](#round-2)). Only 5 of
the 14 are inside a client's own Terraform, Unity Catalog, and dbt stack, which
is where DataForge version 1 works. Most of the others are vendors changing
data that customers consume. Both rounds ran without access to most source
pages, forums, and the dbt-core tracker: the request to allow those hosts was
rejected by the environment service. So 14 is a lower bound. The decision is
in [Recommendation](#recommendation).

## Gate checks

| Check | Target | Result | Status |
|---|---|---|---|
| 1. Independent, dated public cases, last 3 years, structural change across a team boundary that broke data downstream | 15 | 14 strict (11 in round 1, 3 in round 2). 20 loose in round 1 | **Fail by 1** |
| 2. Share of qualifying cases where the existing tools did not catch it | At least 1 in 3 | 10 of 14 not caught, 1 partly, 3 not known (at least 71%) | **Pass** |
| 3. A real gap in the tool landscape, with owners | At least 1 layer combination | Terraform grant or storage change, to Unity Catalog, to dbt, to the owner, on the Terraform PR: no product found. See [tool-landscape.md](tool-landscape.md) | **Pass, medium confidence** |

## How each case was classified

The research agent found 27 cases and counted 20 with "boundary = yes". In
review, each case was tested against all parts of check 1: structural change,
team boundary, and data broken downstream.

| Case | Strict check 1 | Reason | Inside a DataForge v1 stack? |
|---|---|---|---|
| 1 Cloudflare, ClickHouse permissions | Counts | A grant change changed a query output that another system consumed | No (ClickHouse). Same class of change |
| 2 Snowflake schema update | Excluded | A vendor platform outage, not data downstream of a change by a team | No |
| 3 Google Cloud quota policy | Excluded | Service configuration, not data | No |
| 4 HubSpot permissions | Excluded | Application access, not data | No |
| 5 Databricks provider #6197, USE_CATALOG lost | Counts | Grant lost for all consumers, "broke downstream workloads" | **Yes** |
| 6 Databricks provider #5215 | Excluded | Boundary not stated | Yes |
| 7 Databricks provider #5010, warehouse grant removed | Counts | Grant of another principal's workload removed | **Yes** |
| 8 Databricks provider #4679 | Excluded | Boundary and impact not stated | Yes |
| 9 Databricks provider #3582, wrong group | Counts | Consumer groups lost access to schemas | **Yes** |
| 10 Databricks provider #3261 | Excluded | Boundary not stated | Yes |
| 11 Databricks account API field removed | Excluded | Infrastructure code broke. No data broke | Partly |
| 12 Fivetran Terraform provider | Excluded | Infrastructure code broke. No data broke | No |
| 13 Airbyte, renamed column | Excluded | Boundary not stated | No |
| 14 Airbyte Stripe connector | Excluded | Same columns, wrong content: a change in meaning | No |
| 15 Airbyte HubSpot fields dropped | Counts | Fields that users received are silently dropped | No |
| 16 Meta OAuth scope | Excluded | Access setup, not data | No |
| 17 Kyriba API moved | Excluded | Endpoint move, not a data structure | No |
| 18 dbt_shopify package, unique keys changed | Counts | Package owners changed model keys. 3 production models failed | **Yes** |
| 19 Fivetran Postgres column drops | Counts | Vendor change hit views owned by customers | No (Postgres) |
| 20 Fivetran GA4 schema revert | Counts | Columns synced as NULL in customer tables | No |
| 21 Fivetran type change removed masking policy | Counts | Type change removed a governance policy and broke joins | No (Snowflake). Same class |
| 22 Meta Instagram metrics removed | Counts | Fields removed. Reports lost metrics | No |
| 23 Meta Ads attribution windows removed | Counts | Fields and breakdown removed. Custom reports stopped | No |
| 24 Mozilla telemetry columns dropped | Excluded | Caught by a schema check before data broke. A useful positive example | No |
| 25 Wikimedia replica column | Excluded | Boundary not confirmed | No |
| 26, 27 Databricks community, grants lost on replace | Excluded | No confirmed date, boundary not stated | Yes |

## Findings

1. **The failure mode is real, and tools miss it.** In the strict set, the
   existing tools missed 7 of 11 cases. Only 1 case in all 27 was stopped
   before harm (Mozilla), and it was stopped by a schema compatibility check,
   the same idea as DataForge.
2. **The Terraform plan hides permission loss.** In 5 Databricks provider
   issues (#3582, #4679, #5010, #5215, #6197), the plan or diff did not show
   the grants that the apply removed. **Design consequence:** DataForge cannot
   read the plan alone. It must compare live grants with intended grants, and
   model how `databricks_grants` replaces the full set.
3. **Public evidence inside the exact stack is thin.** Only 4 strict cases
   sit in Terraform, Unity Catalog, and dbt. Teams rarely publish "team A
   renamed a column and broke team B" incidents. They stay in private
   incident trackers.
4. **Most public breaks come from vendors.** 7 of the 11 strict cases are SaaS
   or loader vendors. DataForge version 1 does not watch SaaS APIs. It sees
   these changes only when the landed tables are in Unity Catalog.
5. **Changes in meaning are common too** (cases 14, and the rejected dbt
   package issues). Version 1 does not catch them, by design.

## Recommendation

Round 1 set the rule: if check 1 still has fewer than 15 strict cases after
round 2, the gate fails. It has 14. **By the rule, the gate fails**, and
section 12 of the overview applies: DataForge stays a portfolio project.

Do not move the target after the result. 2 facts make the case for a
different decision, and the owner must make that decision openly:

1. **Round 2 did not get the network access it planned.** Reddit, Hacker
   News, dbt Discourse, and blogs stayed blocked.
2. **The count is not the strongest signal.** The stronger signal is that
   only 5 public cases sit inside the exact stack. Teams do not publish
   these incidents. The question "does this happen often enough to pay for a
   tool" needs design partners, not more public cases.

**Proposed decision:** accept the fail. DataForge continues as a portfolio
project:

- Phase 1 (the reference platform on Azure) goes ahead, because the Terraform
  is ready and the project is useful as public proof.
- The product question moves to the week 10 check. If 2 design partners run
  the CLI on a real repository, the product case opens again with private
  evidence, which public cases cannot give.
- No product features are built before that (rule 3).

Design inputs from the research stand either way:

- Compare live grants with intended grants. The Terraform plan alone hides
  permission loss (round 1 finding 2).
- Watch dbt changes that remove policies owned by someone else (round 2
  near-miss, dbt-databricks #1782).
- Columns used through inline lists are invisible to `ref` lineage (case 28).

## Evidence log

Fields as in [method.md](method.md). Columns "Layer", "Boundary", and "Would
DataForge v1 catch it" are the research agent's reading. The strict
classification above overrides "Boundary" for the gate count.

Verification labels: "issue body read (API)" means the issue text was read
from the GitHub search API. "search snippet only" means only text quoted in
search results was seen. In review, 4 GitHub cases (#3582, #5010, #6197,
dbt_shopify #80) and 2 web cases (Cloudflare, Snowflake) were checked again
and agree with the log.

| # | Source (URL) | Title/short description | Date | Source type | Layer that changed | Crossed a team boundary | How it was found | Time to find | Caught by a tool the team had | Would DataForge v1 catch it | Verification |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | https://blog.cloudflare.com/18-november-2025-outage/ (also https://www.infoq.com/news/2025/11/cloudflare-global-outage-cause) | A database permissions change in ClickHouse made a metadata query return duplicate rows from a second database (r0). The Bot Management feature file doubled, passed a proxy limit, and core traffic failed worldwide. | 2025-11-18 | independent (first-party postmortem) | other: database grants/permissions, which changed query metadata output | yes: a database access change broke a separate system (Bot Management) that consumed the query output | Widespread 5xx errors. Team first suspected a DDoS attack. | Change deployed about 11:05 UTC, failures from 11:20 UTC. About 6 hours to full recovery (secondary report). | no | partly: grant change is the right class, but ClickHouse is not a supported system and the break was in a query result, not a schema | search snippet only |
| 2 | https://status.snowflake.com/incidents/xdxj4klf7sc5 and https://www.theregister.com/2025/12/18/snowflake_update_caused_a_blizzard/ | Snowflake release shipped a backward-incompatible database schema update. Older release packages referenced the changed schema. Customers in 10 of 23 regions could not query or load data. | 2025-12-16 | independent (first-party status page plus press) | other: vendor internal metadata schema | yes: vendor change broke all downstream customer pipelines | Customer-facing errors (version mismatch) | 02:55 to 15:59 UTC, about 13 hours. Fixed by rollback. | no: passed staged deployment | no: vendor-internal change, outside any customer metadata | search snippet only |
| 3 | https://status.cloud.google.com/incidents/ow5i3PPK96RduMcb1SsW and https://simonwillison.net/2025/Jun/14/google-cloud-outage-incident-report/ | A quota policy change with blank fields was written to Spanner tables that Service Control reads. It replicated in seconds and crashed Service Control in every region. | 2025-06-12 | independent (first-party report) | other: policy metadata (structure of a config record) | yes: one team's policy data broke a shared service used by many teams and customers | Global API failures | 10:51 to 18:18 US/Pacific | no: code path had no error handling or feature flag | no: not a data platform object | search snippet only |
| 4 | https://product.hubspot.com/blog/hubspot-incident-report-february-25-2026 | Permissions framework config went live before matching role assignments were promoted. Access control fell back to restrictive, users lost workflow access. | 2026-02-25 | independent (first-party report) | other: permissions/role configuration | yes: platform permissions change broke access for product users | User impact on workflows | Rollback at 4:20 PM EST. About 29 minutes total (third-party tracker, data inconsistent). | no: HubSpot is now adding pre-deploy checks | partly: same class (permission change without matching grants), but not a supported system | search snippet only |
| 5 | https://github.com/databricks/terraform-provider-databricks/issues/6197 | Changing `databricks_grants` on a catalog revoked USE_CATALOG from "account users" even though the plan showed it unchanged. "In our case this broke downstream workloads until the privilege was granted again." | 2026-11-16 | independent | Terraform or grants (Unity Catalog) | yes: grant for all consumers ("account users") was lost | Apply error after 1 minute, plus downstream workloads failing | Not known (minutes to hours implied) | no: Terraform plan showed the privilege as unchanged | partly: DataForge would see a grants change on a catalog with many consumers, but only if it models the provider's revoke-then-grant behavior, since the plan hid the loss | issue body read (API) |
| 6 | https://github.com/databricks/terraform-provider-databricks/issues/5215 | Applying table-level `databricks_grants` silently revoked catalog-level grants managed by a separate resource. "Observed in a production environment." Plan showed no change to catalog grants. | 2025-11-13 | independent | Terraform or grants (Unity Catalog) | not known: separate resources, likely different consumers, not stated | Unexpected permission loss in production | not known | no: plan did not show the revocations | partly: would flag if it compares live grants with intended grants, not from the plan alone | issue body read (API) |
| 7 | https://github.com/databricks/terraform-provider-databricks/issues/5010 | Adding a SQL warehouse permission for a new service principal removed the existing grant for another service principal. Diff showed only the addition. "Similar issues have happened in various occasions." | 2025-09-08 | independent | Terraform or grants (Databricks permissions) | yes: the removed grant belonged to another principal's workload | After deployment, permission found removed | not known | no: Terraform diff and code review missed it | partly: needs live ACL comparison; plan shows only an add | issue body read (API) |
| 8 | https://github.com/databricks/terraform-provider-databricks/issues/4679 | `databricks_grants` on all external locations replaced existing grants. Plan output did not show what would be removed. Author notes `databricks_grant` vs `databricks_grants` is a 1-letter mistake. | 2025-04-29 | independent | Terraform or grants (Unity Catalog external locations) | not known: existing grants of other principals were overwritten, impact not stated in the part I read | After apply | not known | no: plan was "dangerous and uninformative" | partly: same as #6 | issue body read (API), partial |
| 9 | https://github.com/databricks/terraform-provider-databricks/issues/3582 | `databricks_grants` gave schema permissions to the wrong group on 2 of about 30 schemas, not shown in plan or state. "We just find out when users report they've lost access." | 2024-05-15 | independent | Terraform or grants (Unity Catalog schema) | yes: consumer groups lost access | User reports | not known | no: not visible in plan or state | partly: only if it reads live grants; config looks correct | issue body read (API) |
| 10 | https://github.com/databricks/terraform-provider-databricks/issues/3261 | After redeploying external locations, a group with ALL PRIVILEGES could see only 8 of 10 external locations. | 2024-02-14 | independent | Terraform or grants (Unity Catalog external locations) | not known | Users or admin noticed missing locations | not known | not known | partly: grants on moved/recreated objects is in scope | issue body read (API), partial |
| 11 | https://github.com/databricks/terraform-provider-databricks/issues/5675 | Databricks account API response no longer had `workspace_url` (only `workspace_fqdn`). Terraform planned to recreate a RUNNING workspace and its dependent resources. Downstream workspace providers failed auth. | 2026-05-01 | independent | other: vendor API response shape, seen through Terraform | yes: vendor API change broke customer infrastructure code | terraform plan showed workspace "deleted" | at plan time | partly: plan showed the destroy, but nothing explained the cause | partly: would flag a planned destroy of a workspace with dependents, not the cause | issue body read (API) |
| 12 | https://github.com/fivetran/terraform-provider-fivetran/issues/643 | Fivetran API started returning 2 extra fields (`sheet_name`, `cell_number`) on S3 connection config after Excel support shipped. Terraform apply fails. | 2026-10-08 | independent | other: vendor API schema, seen through Terraform | yes: vendor change broke customer Terraform | apply failure | not known | no | no: vendor API outside scope | issue body read (API) |
| 13 | https://github.com/airbytehq/airbyte/issues/54719 | A column was renamed in a Postgres source. Airbyte deleted the old column in Snowflake, so historical data was lost. The new column stayed NULL for old rows. | 2025-02-28 | independent | source schema | not known: source owner not stated | Noticed data loss in destination | not known | no: the sync tool caused the loss | partly: source column rename is the right class; Postgres and Snowflake are not supported systems | issue body read (API) |
| 14 | https://github.com/airbytehq/airbyte/issues/59154 | source-stripe 5.11 release changed invoice_lines handling. Rows got the invoice id instead of the line item id and lost line data. | 2025-04-29 (started 2025-04-25) | independent | other: connector release changed row structure | yes: connector maintainers' release broke user data | User inspected data | about 4 days (25 Apr to 29 Apr) | no | no: same columns, wrong content | issue body read (API) |
| 15 | https://github.com/airbytehq/airbyte/issues/82771 | HubSpot properties returned by the API but not in the stream schema used to land in a catch-all column. New V2 destinations drop them silently. | 2026-07-27 | independent | source schema (connector/destination schema handling) | yes: destination maintainers' change removed fields users received before | User investigation | not known | no: silent drop | no: outside scope (partly if landed tables are in Unity Catalog) | issue body read (API) |
| 16 | https://github.com/airbytehq/airbyte/issues/71263 | Meta rejects the `read_insights` OAuth scope that the Facebook Marketing connector requests, so login fails. | 2026-01-09 | independent | other: vendor permission scope | yes: SaaS vendor change broke connector setup | Login error | at setup | no | no | issue body read (API), partial |
| 17 | https://github.com/airbytehq/airbyte/issues/75948 | Kyriba moved its API platform (new OAuth and API URLs). Syncs failed. | 2026-03-31 | independent | other: vendor API endpoints moved | yes: SaaS vendor change | Sync failure | not known | no | no | issue body read (API) |
| 18 | https://github.com/fivetran/dbt_shopify/issues/80 | dbt_shopify package 0.12.0 changed unique keys of incremental models. Existing tables lacked the new key columns: "invalid identifier 'ORDERS_UNIQUE_KEY'". 3 production models failed. | 2024-05-02 | independent | dbt model (third-party package) | yes: package maintainers changed model structure used by consumers | dbt run failed | about 1 hour after upgrade | no: failed at run time, not before | yes: dbt model column/key change against an existing table, if both projects are read | issue body read (API) |
| 19 | https://status.fivetran.com/incidents/qtns030fy6mh (mirror: https://isdown.app/status/fivetran/incidents/305060-connectors-to-postgres-destinations-are-failing-with-an-alert-drop-deprecated-non-null-column) | A Fivetran change misread string columns as type changes and tried to drop and recreate them. Drops failed where customer views referenced the columns. Customers had to drop and recreate views. | 2024-08-01 to 2024-08-03 | independent (first-party postmortem) | source schema (loader changed destination columns) | yes: vendor change hit customer-owned views | Connector failures and dashboard alerts | about 2 days to resolve | partly: Postgres view dependencies blocked the drop | partly: right class (drop of a column with downstream views), Postgres not supported | search snippet only |
| 20 | https://status.fivetran.com/incidents/55s8gt1f2dbt | GA4 Export connectors reverted to an older schema. Event tables synced NULLs for `params` and `user_properties`. | 2025-04 | independent (first-party status page) | source schema | yes: vendor change affected customer tables | not known | not known | not known | partly: source schema change class | search snippet only |
| 21 | https://support.fivetran.com/hc/en-us/community/posts/42521291100055-Alert-Notify-on-Data-Type-Changes-for-Columns-with-Snowflake-Masking-Policies-Applied-instead-of-silent-drop-and-recreate | Source column changed TEXT to VARIANT. Fivetran did add/copy/rename/drop, which removed the Snowflake masking policy. Reporter says protected data can be exposed and downstream joins can return wrong results silently. | 2026-07-30 | independent | source schema (type change) that also removed a governance policy | yes: source owner change plus vendor loader action hit the customer's governance | Customer found it (method not stated) | not known | no: "no signal from Fivetran" | partly: type change and lost policy are both in scope in Unity Catalog terms, but Snowflake is not supported | search snippet only |
| 22 | https://developers.facebook.com/docs/graph-api/changelog/version22.0 and https://docs.emplifi.io/platform/latest/home/instagram-insights-metrics-deprecation-april-2025 | Meta removed Instagram `impressions`, `plays`, `video_views`. Requests for newer media return an error after 2025-04-21. Reporting tools lost metrics and remapped to `views`. | 2025-04-21 | independent | source schema (SaaS API fields removed) | yes: SaaS vendor removed fields | Announced in advance | n/a (planned) | not known | no: outside scope | search snippet only |
| 23 | https://developers.facebook.com/blog/post/2025/10/16/ads-insights-api-metric-availability-updates/ and https://fivetran.com/docs/connectors/applications/facebook-ads/changelog | Meta stopped returning 7-day view and 28-day view attribution in Ads Insights. Fivetran also removed the `dma` breakdown, and custom reports using it stopped syncing. | 2026-01-12 | independent | source schema (SaaS API fields and breakdown removed) | yes: SaaS vendor | Announced in advance | n/a (planned) | not known | no: outside scope; part of the impact is a meaning change (lower numbers) | search snippet only |
| 24 | https://bugzilla.mozilla.org/show_bug.cgi?id=1898105 | A Firefox ping change (bug 1897506) dropped columns. The probe-scraper schema job flagged "incompatible changes". Fix: allow it once, regenerate schemas, revert allowlist. | 2024-05 | independent | source schema (telemetry ping) | yes: product instrumentation change hit the data platform | Schema-generation CI check | at deploy time | yes: schema compatibility check | partly: same idea as DataForge, not its systems | search snippet only |
| 25 | https://phabricator.wikimedia.org/T409282 | A column was missing in a wiki replica table because a schema change was not fully applied. Fix deployed 2025-11-05. | 2025-11 | independent | source schema | not known: replica consumers likely differ from schema owners, not confirmed | Probably user report (not confirmed) | not known | not known | partly: missing column class | search snippet only |
| 26 | https://community.databricks.com/t5/data-governance/create-or-replace-view-removes-permissions-unity-catalog/m-p/49602 | CREATE OR REPLACE VIEW on a Unity Catalog view removed its grants. A user called it a race condition in CI/CD and switched to ALTER VIEW. | date not confirmed (thread has later replies) | independent | Terraform or grants (Unity Catalog view grants lost on replace) | not known: grantees likely other teams, not stated | Users lost access | not known | no | partly: grants loss on object replace is in scope if DataForge models replace semantics | search snippet only |
| 27 | https://community.databricks.com/t5/data-governance/unity-catalog-functions/m-p/138047 | CREATE OR REPLACE FUNCTION drops the function's grants (Databricks employee reply). Workaround: grant at schema or catalog level. | date not confirmed | independent | Terraform or grants (Unity Catalog function grants) | not known | User question after lost EXECUTE grants | not known | not known | partly: same as #26 | search snippet only |

## Rejected candidates (researcher's list)

| Candidate | Why rejected |
|---|---|
| Uber D3 blog, https://www.uber.com/blog/d3-an-automated-system-to-detect-data-drifts (Feb 2023) | Too old. Useful context only: partial-data incidents took about 5 times longer to detect than ETL failures. |
| VentureBeat "most pipeline monitoring checks if the job ran..." (ad network renamed a field, counts off 40%) | Could not open or confirm the text, date or author. Unclear if first-person. |
| Kevin Holland post (vendor renamed an API field, dashboards showed zero for 6 hours) | Only seen as a search summary. Page not found on a second search. Not verifiable. |
| Bigeye blog "how bigeye detected issues that our dbt ci jobs missed" | Vendor, and the change was their own seed file, not a boundary. |
| Monte Carlo, Datafold, Gable, Acceldata pages from searches | Vendor marketing and generic or hypothetical examples. |
| dev.to, HackerNoon, Medium, DZone articles (for example "How a field rename broke 19 restaurants for a week", "That time one field change took down an entire production pipeline", "What I learned from reading 50 data pipeline postmortems") | dev.to was blocked. Could not confirm date, author or if the story is real. Several are generic or illustrative. |
| dbt Discourse "All incremental models started failing yesterday" and dbt-labs/dbt-adapters#958 (2025-04) | Same event. An adapter code bug (SQL alias on Redshift), not a structural data or grant change. |
| Segment status "Snowflake RETL sources and Warehouse Destinations are failing due to Snowflake Outage" | Duplicate of Snowflake case #2. Shows the knock-on effect. |
| fivetran/dbt_instagram_business issues #17, #19, #24 | Duplicate of Meta case #22 (package-side deprecation notices). |
| Databricks community "Schema changes notification" and "Data contracts on Databricks" threads | Questions about practice, no incident. |
| Metabase Discourse "How do you handle schema changes breaking dashboards?" | Could not open. Date and incident details unknown. |
| Microsoft Q&A on Azure cost export column change breaking Power BI | 2021, too old. |
| Red Hat Jira COST-4662, COST-5367 (Azure export column names) | Adaptation work. No incident details visible. |
| microsoft/finops-toolkit #873, #874, #2158 | Missing export columns or refresh errors, but no clear downstream incident or cause in the text I saw. |
| dbt Cloud status write-ups 2025 and 2026 | Internal vendor incidents (credentials, DNS, node updates), not cross-team structural data changes. |
| Unkey Aug 2025 (permissions deleted by a logic bug) | Internal product bug, not a data-platform boundary. |
| Mozilla bugs 1883727, 1876620 | Deployment ordering problems, not a boundary change. |
| Wikimedia T355588 | DAG paused while waiting for schema rollout. No break. |
| terraform-provider-databricks #4411, #5360, #4025 | Tool bugs with no downstream break. |
| databricks-sdk-py issues, unitycatalog OSS issues | Not structural data changes. Mostly questions or feature requests. |
| fivetran/dbt_iterable #41, fivetran/dbt_zendesk_source #47 | Meaning (semantic) problems with the same schema. Out of v1 scope. Worth noting as evidence that semantic issues are common too. |
| fivetran/dbt_hubspot #158 | Duplicate column after a package change only with a special config. Weak, closer to a package bug. |

## Bias and gaps (researcher's notes)

- Selection bias: public sources over-sample vendor outages and tool bugs. Internal "team A renamed a column and team B broke" stories mostly live in private Slack and incident trackers. I found almost none as clean public postmortems in the exact DataForge stack.
- Stack gap: Unity Catalog, Terraform and dbt evidence is mostly GitHub issues about provider behavior. They show the risk (grants lost, plans that hide removals) but often do not say who owned the broken consumer.
- Azure gap: I found no dated Azure case that met the bar. Azure cost export changes look relevant but the evidence was too old or too thin.
- Source access: WebFetch was blocked for every host, so 13 cases rest on search snippets. dbt-labs/dbt-core issues could not be searched. Reddit and Hacker News threads never appeared in results, so practitioner first-person stories are under-represented.
- "Caught by a tool" is often not stated. I marked "no" only when the text says the tool missed it or the break was found by impact.
- "Boundary = yes" sometimes rests on reasonable reading (for example, a vendor changing an API). Where the text did not say, I wrote "not known".
- No frequency data: these cases show the failure mode is real and tools miss it, but they cannot tell how often it happens per team per year.

## Round 2

Date: 22 November 2026. Done with GitHub issue search and web search only. No
round 1 case is logged again. In review, cases 28 and 30 were checked again
from the GitHub API and agree with the log.

Review notes:

- **Case 28** is strong: a vendor feed dropped and renamed columns, and a dbt
  build on Databricks failed.
- **Case 29** is borderline: the cause comes from search snippets of the fix
  pull request.
- **Case 30** is borderline on the boundary: the PR says "Looker renamed
  three fields", but it does not name the owner of the Looker model.

### New strict cases

Verification labels: "issue body read (API)" and "PR body read (API)" mean the full text came from the GitHub search API. "search snippet only" means only text in a search result was seen.

| # | Source (URL) | Short description | Date | Source type | Layer that changed | Boundary (who changed, who broke, evidence) | How it was found | Time to find | Caught by a tool the team had | Would DataForge v1 catch it | Inside a DataForge v1 stack | Verification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 28 | https://github.com/thegoodparty/gp-data-platform/pull/974 | Good Party's data vendor (Haystaq) stopped shipping 100 columns in its feed. 28 of them were renames, for example `hs_immigration_undesirable` became `hs_illegal_imm_undesirable`. The scheduled dbt build on Databricks failed on `m_election_api__district_top_issues` with `UNRESOLVED_COLUMN`. An earlier fix (#972) missed this model because it kept its own inline column list, so `state:modified+` never selected it. | 2026-09-09 | independent (first-party PR in a company repo) | source schema (vendor feed columns dropped and renamed) | Vendor changed, Good Party data team's mart broke. Quote: "it kept naming 17 columns the vendor no longer ships". Also: "Two are vendor renames". | Scheduled `dbt build` job failed | not known ("has been failing") | no: dbt `state:modified+` did not select the model. The job failed at run time | partly: the change came from a vendor feed, not a PR. A metadata diff of the Unity Catalog source view against compiled dbt column use would list this model. The inline column list hides it from `ref` lineage | **yes** (Databricks Unity Catalog, dbt) | PR body read (API) |
| 29 | https://github.com/microsoft/finops-toolkit/issues/2332 (cause: https://github.com/microsoft/finops-toolkit/pull/2333 and https://techcommunity.microsoft.com/blog/finopsblog/introducing-non-breaking-%E2%80%9Cbreaking%E2%80%9D-changes-in-finops-hubs-12/4438554) | A customer's FinOps toolkit Power BI storage reports fail to load: "The column 'SkuMeterName' of the table wasn't found." In FOCUS 1.2 Cost Management exports and FinOps hubs 12, Microsoft renamed `x_SkuMeterName` to `SkuMeter`. The fix PR says the FOCUS 1.2 branch of the report query used the wrong name, and CI never runs Power Query. An earlier report with the same error: https://github.com/microsoft/finops-toolkit/issues/1798 (2025-08-08, cause not confirmed). | 2026-09-21 | independent (Microsoft open source repo, customer report) | source schema (Azure Cost Management export column renamed) | Microsoft (export schema owner and toolkit maintainers) changed, customer's reports broke. Paraphrased: the reporter changed nothing; the rename is in Microsoft's FOCUS 1.2 / hubs 12 release ("x_SkuMeterName is now SkuMeter"). | Power BI refresh error seen by the customer | not known | no: per the fix PR, CI never runs Power Query, so the wrong name went unnoticed | no: Power BI semantic models and Cost Management exports are outside v1 metadata | partly (Azure source, Power BI consumer) | issue body read (API); cause from search snippets of PR #2333 and the Microsoft blog |
| 30 | https://github.com/ProcurementAtOdeko/OdekoDashboards/pull/101 | Looker renamed 3 fields in the exports that Odeko's procurement sales trackers read (`SO Amount` became `Sales Order Line Amount`, and 2 more). Every market failed its column check and silently kept its last snapshot. The workflow exited 0. Dashboards served data frozen at 2026-10-28 for 13 days. | 2026-10-28 (break), 2026-11-10 (fix) | independent (first-party PR in a company repo) | source schema (BI export field names renamed) | Looker export owner changed, procurement dashboards broke. Quote: "Looker renamed three fields in the exports" and "the exports changed underneath us". | Not stated. The PR adds guards because "nobody noticed" | 13 days | no: "Thirteen days of hourly runs, all green" | no: Looker exports and a custom dashboard repo are outside v1 | no | PR body read (API) |

### Near-misses (each failed exactly 1 strict test)

| Source (URL) | What happened | Failed test | Why |
|---|---|---|---|
| https://github.com/databricks/dbt-databricks/issues/1782 | Since dbt-databricks 1.12.0, a `table` rebuild drops Unity Catalog row filters that an admin or governance tool applied outside dbt. Every user with SELECT can then read all rows. (2026-11-19) | 1 | Reproduced on a demo table (`demo_db`). No production event is described. Strong design signal for DataForge: a dbt change removes a policy owned by someone else |
| https://github.com/cal-itp/data-infra/issues/3283 | A new Airtable column whose name starts with a number broke BigQuery external table creation and downstream dbt models "for a couple days". (2024-02-21) | 3 | The issue says "unhandled column in the source Airtable" but does not say who added it or that it was another team |
| https://github.com/cal-itp/data-infra/issues/3757 | Airtable field `rtpa` became an array. The staging model `stg_transit_database__organizations` broke. (2025-03-08) | 3 | Who changed the Airtable field is not stated |
| https://github.com/cal-itp/data-infra/issues/3809 | Airtable field `products` became repeated. `int_transit_database__contracts_dim` failed. (2025-04-04) | 3 | Who changed the field is not stated (Sentry bot issue) |
| https://github.com/mozilla/bigquery-etl/pull/9916 | A source ping moved to OHTTP, so `client_info` no longer existed. Contextual services queries were fixed to read `normalized_channel` from the root. (2026-09-23) | 3 | PR body is 1 sentence. The ping owner is implied ("upstream schema"), not named |
| https://github.com/thegoodparty/gp-data-platform/pull/1408 | Column `properties_win_number` disappeared from the raw Airbyte HubSpot companies table (last write 2026-03-19). Found on 2026-11-20 when a fresh CI schema failed. | 3 | Says "the next narrowing of the upstream stream" but not who narrowed it (HubSpot owner, connector, or own config) |
| https://github.com/thegoodparty/gp-data-platform/pull/1363 | gp-api (app team) moved the onboarding entry screen. Event names changed, a dbt test failed every nightly since about 2026-11-05, and 10 models were skipped. | 2 | Event values changed, not the schema |
| https://github.com/thegoodparty/gp-data-platform/pull/1270 | Vendor L2 changed district name spelling and HubSpot gained a dropdown option. 43 models were skipped on every nightly from 2026-10-24. | 2 | Value changes with the same schema |
| https://github.com/thegoodparty/gp-data-platform/pull/1353 | gp-api planned to drop `campaign.ai_content`. The data team removed it from dbt first, because staging and everything downstream would fail. (2026-11-11) | 4 | Caught before harm. A useful positive example: a cross-team column drop handled by advance notice |
| https://github.com/thegoodparty/gp-data-platform/pull/1019 | Airbyte forced its Databricks destination to Direct-Load, which stops writing raw tables. 16 models would have gone stale silently. Fixed in advance. (2026-09-17) | 4 | Caught before harm |
| https://github.com/thegoodparty/gp-data-platform/pull/1208 | An internal rename (#1068) of Stripe staging columns broke `topline_report.py` for 3 weeks. (2026-10-15) | 3 | Same data team on both sides, as far as the PR shows |
| https://github.com/thegoodparty/omni/pull/3525 | Product event `Outreach - SMS Cutoff Notice Viewed` stopped firing for 2 weeks. Nothing alerted. (2026-11) | 2 | An app bug stopped an event. Not a schema change |
| https://github.com/microsoft/finops-toolkit/issues/1905 | Toolkit v1_2 transform renamed columns. Older exports land with `SkuMeter` and `PricingCurrency` NULL. (2025-12-14) | 1 | Bug report with repro steps. No production impact is described |
| https://github.com/fivetran/dbt_stripe/issues/104 | Package model referenced `created_at`, the source has `created`. Downstream models fail to compile. (2025-01-30) | 1 | No production run or impact is stated |
| https://github.com/databricks/dbt-databricks/issues/1662 | Incremental full refresh on managed Iceberg runs DROP then CREATE. The table is missing for about 3m40s, concurrent queries fail, grants survive only if inherited. (2026-09-01) | 3 | Who ran the failing queries is not stated |
| https://github.com/hashicorp/terraform-provider-azurerm/issues/28169 | Moving from deprecated `storage_account_name` to `storage_account_id` made the plan replace storage shares and containers. (2024-12-03) | 4 | Seen at plan time. No data was lost or broke |

Also seen but weaker (failed more than 1 test, or not verifiable): airbytehq/airbyte#93987 (Google Ads v24 field removal, predicted only), airbytehq/airbyte#42846 (LinkedIn metric deprecated, a meaning change), microsoft/finops-toolkit#2311 (price sheet schema version, search snippet only, no date seen), dbt-databricks#1755, a dev.to post "Schema Drift: The Silent Pipeline Killer" (no date, author may sell a tool), a dev.to post on a table swap that dropped orders from Postgres logical replication (no date, boundary not stated), Databricks Community thread 166942 (streaming tables failed after a bronze schema change; snippet only, boundary not stated).

### Counts

| Item | Count |
|---|---|
| New strict cases | 3 (#28 to #30) |
| Of these, inside a DataForge v1 stack | 1 yes (#28), 1 partly (#29), 1 no (#30) |
| Of these, not caught by the team's tools | 3 of 3 |
| Strict total with round 1 | 14 (target 15) |
| Strict cases inside the stack, total | 5 (round 1: 4, round 2: 1) |
| Near-misses (failed 1 test) | 16 |
| GitHub search API calls | 26 (1 refused for a missing `is:` qualifier, 1 refused because the repo does not exist) |
| Web searches | about 45, mostly "extended" mode |

### Problems hit

- WebFetch failed (discourse.getdbt.com did not resolve). No page reads were possible.
- WebSearch refuses `reddit.com` as an allowed domain (HTTP 400). No Reddit thread appeared in any result. Hacker News results were advice threads, not incidents.
- `gh api repos/<owner>/<repo>/...` (direct issue reads) returned 403 for repos not attached to the session. Only `search/issues` worked, so comments on issues could not be read.
- Open web results were mostly vendor blogs, how-to guides and illustrative stories with no date. Almost no company postmortem about a cross-team schema change was found.
- The best new source was public company data repos with detailed PR descriptions (Good Party, Cal-ITP, Odeko, Mozilla). They describe real breaks, but often do not say who made the upstream change, so many fail test 3.
- Some of these PR descriptions were written with an AI coding assistant. They are still first-party records of real events in the company's repo.

### Leads for a round 3

- More public company data repos with detailed PRs: search `is:pr` in thegoodparty, cal-itp, mitodl, mozilla/bigquery-etl with words like "vendor", "upstream", "no longer ships", "renamed in the source".
- Read comments on cal-itp/data-infra #3283, #3757, #3809, #4339. A comment may name the Airtable owner and turn a near-miss into a strict case (this needs direct issue reads, which were blocked).
- microsoft/finops-toolkit: other customer reports after the hubs 12 and FOCUS 1.2 renames.
