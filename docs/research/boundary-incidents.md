# Boundary incidents: evidence log and gate result

Date: 22 November 2026
Done by: Claude (desk research, with 3 research agents and 1 review pass)
Method: [method.md](method.md)

## Result in 1 paragraph

**The gate is not passed yet. 2 of 3 checks pass. Check 1 is open.**
Under a loose reading, 20 public cases cross a team boundary. Under the strict
reading of check 1 ("a structural change crossed a team boundary and broke
data downstream"), only 11 cases qualify, and the target is 15. Only 4 of
the 11 are inside a client's own Terraform, Unity Catalog, and dbt stack, which
is where DataForge version 1 works. The other 7 are vendors (SaaS APIs,
loaders) changing data that customers consume. Network limits in this
research session blocked most source pages, community forums, and the dbt-core
issue tracker, so the count is a lower bound. The decision is in
[Recommendation](#recommendation).

## Gate checks

| Check | Target | Result | Status |
|---|---|---|---|
| 1. Independent, dated public cases, last 3 years, structural change across a team boundary that broke data downstream | 15 | 11 strict (20 loose) | **Open** |
| 2. Share of qualifying cases where the existing tools did not catch it | At least 1 in 3 | 7 of 11 not caught, 1 partly, 3 not known (at least 64%) | **Pass** |
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

Do not stop the product on this result, and do not pass the gate either.
The shortfall comes partly from the research setup, not only from the world:

- Reddit and Hacker News returned no threads.
- dev.to and most blogs could not be opened.
- The dbt-core issue tracker could not be searched.
- 13 cases rest on search snippets only.

**Next step:** a second round of 1 week (inside the week 2 deadline in
section 12 of the overview), with network access to the source hosts. It
targets:

1. dbt-core issues and dbt Discourse threads about upstream changes.
2. r/dataengineering and Hacker News first-person accounts.
3. Page reads of the 13 snippet-only cases.

If check 1 still has fewer than 15 strict cases after that round, the gate
fails, and section 12 applies: DataForge stays a portfolio project.

Desk research cannot answer the frequency question. These cases show that the
failure exists, not how often it happens. Only design partners can supply
that (the week 10 criterion).

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
