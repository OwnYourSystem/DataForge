# Survey sources for the DataForge overview

> **Review note (22 November 2026).** Written by a research agent and reviewed
> by Claude. Every row comes from search result text, because this research
> session could not open the source pages. Read the page before you quote a
> row in public (rule 1). Overview: [boundary-incidents.md](boundary-incidents.md).


Date of research: 2026-11-22.

## How this was checked

- WebFetch was blocked for every host tried (getdbt.com, montecarlodata.com, montecarlo.ai, joereis.github.io). No page could be read in full.
- So every figure below comes from WebSearch result text only. All rows are marked "search snippet only".
- Where a snippet came from a third party and not the publisher, the row says so.
- "Vendor" means the survey was run or paid for by a company that sells a data tool.

## Verdicts on the 2 overview claims

### Claim 1: "Unclear ownership is a top pain point in 3 surveys (39% to 51%)."

Verdict: **confirmed with correction.**

- The 51% end is real. It is the Practical Data 2026 State of Data Engineering survey (Joe Reis): "Lack of clear ownership" 50.7%.
- The 39% end was **not found**. No survey we found gives 39% for unclear ownership. The 39% figures we found are about other things (for example dbt 2025 data literacy, Thales data classification, Drexel governance obstacles).
- The lowest ownership figure we found is 41% (dbt Labs 2026).

Corrected wording (recommended, 3 different publishers):

> Unclear ownership is a top pain point in 3 surveys (41% to 51%): dbt Labs 2026 (41%), a Secoda 2025 webinar poll (47%) and the Practical Data 2026 survey (51%).

The Secoda figure is a live webinar poll, not a formal survey. If you want only formal surveys, use this set instead (2 publishers):

> Unclear ownership is a top pain point in 3 surveys (41% to 51%): dbt Labs 2026 (41%), dbt Labs 2024 (almost 50%) and the Practical Data 2026 survey (51%).

A 4th data point exists: dbt Labs 2023 put it at 43%, but we only saw that in a third-party blog (Synq) and in the dbt 2024 report's "up from last year's 43%" line.

Short safe version: "Unclear ownership is a top pain point in several surveys (41% to 51%)."

### Claim 2: "Source-side causes (ingestion disruptions and schema drift) are about 24% of incidents in the only root-cause data we found. That data comes from a vendor."

Verdict: **confirmed with correction.**

- Monte Carlo's blog "Data Quality Statistics & Insights From Monitoring +11 Million Tables" lists ingestion disruptions at 16.6% and schema drift at 7.8%. Together that is 24.4%. So "about 24%" is right.
- It is not a survey. It comes from root causes found by Monte Carlo's Troubleshooting Agent across its own customers ("run thousands of times across hundreds of customer environments"). We did not find the exact number of incidents.
- "The only root-cause data we found" is a bit too strong. A Bigeye-linked survey on Dataversity found 31% of 100 respondents named upstream changes as their most common data quality issue. That is a different measure (most common issue, not share of incidents), but it is related.

Corrected wording:

> Source-side causes (ingestion disruptions 16.6% and schema drift 7.8%) are about 24% of the data quality incidents whose root cause Monte Carlo's AI agent identified across its customers. This is a vendor's own platform data, not an independent survey. It is the only incident-level root-cause breakdown we found.

## Evidence table

| Claim | Exact figure and wording from source | Publisher | Who ran it (vendor?) | Sample size | Year | URL | Verified from |
|---|---|---|---|---|---|---|---|
| Ownership | "Ambiguous data ownership remains a challenge for 41% of respondents, effectively unchanged year over year." Also: 41% of practitioners and 40% of leaders. | dbt Labs, 2026 State of Analytics Engineering | dbt Labs (vendor) | 363 (survey Dec 5, 2025 to Feb 1, 2026) | 2026 | https://www.getdbt.com/resources/state-of-analytics-engineering-2026 | search snippet only |
| Ownership | "'Ambiguous data ownership' was the second most frequently cited challenge, highlighted by almost 50% of respondents." Also: "increased from last year's 43%". No exact decimal found. | dbt Labs, 2024 State of Analytics Engineering | dbt Labs (vendor) | 456 (survey Dec 22, 2023 to Mar 2, 2024; margin of error +/- 5.6%) | 2024 | https://www.getdbt.com/resources/state-of-analytics-engineering-2024 | search snippet only |
| Ownership | 43% said ambiguous data ownership was their biggest challenge when preparing data. | dbt Labs, 2023 State of Analytics Engineering (as cited by Synq) | dbt Labs (vendor); citation by Synq (vendor) | Not found | 2023 | https://www.synq.io/blog/data-ownership-guide | search snippet only (third-party citation) |
| Ownership | Data modeling pain points table: "Lack of clear ownership: 50.7%". Substack: "51% say lack of ownership"; "59% cite pressure to move fast". | Practical Data, 2026 State of Data Engineering Survey | Joe Reis / Practical Data community (not a tool vendor; independent author and consultancy) | 1,101 (Dec 2025 to early Jan 2026, via Practical Data community and LinkedIn) | 2026 | https://joereis.github.io/practical_data_data_eng_survey/ and https://joereis.substack.com/p/the-2026-state-of-data-engineering | search snippet only |
| Ownership | 74.5% have no dedicated owner for data products. | Joe Reis Substack, follow-up on the 2026 survey | Joe Reis (not vendor) | 1,101 | 2026 | https://joereis.substack.com/p/the-data-anarchy-tax-why-your-team | search snippet only |
| Ownership | About 47% named "unclear ownership and accountability" as the primary blocker to scaling governance. | Secoda blog, "Data governance in 2025: What the polls tell us" | Secoda (vendor); live webinar poll | "Hundreds of data leaders" (no exact number) | 2025 | https://www.secoda.co/blog/data-governance-survey | search snippet only |
| Ownership | 32% of CFOs name lack of data ownership as a key barrier. | PR Newswire release, "Companies Are Scaling AI on Data They Don't Trust" | Sponsor not confirmed in snippet | Not found (fielded Mar 16 to 19, 2026) | 2026 | https://www.prnewswire.com/news-releases/companies-are-scaling-ai-on-data-they-dont-trust-new-study-finds-302761641.html | search snippet only |
| Root cause | Ingestion disruptions 16.6%; schema drift 7.8% ("highlights the ongoing tension between agility and control"); platform instability 15.2%; intentional changes such as backfills 14.2%; real-world variation 20%; "approximately 34% of data quality incidents actually aren't incidents". | Monte Carlo blog, "Data Quality Statistics & Insights From Monitoring +11 Million Tables" | Monte Carlo (vendor); Troubleshooting Agent telemetry, not a survey | Agent "run thousands of times across hundreds of customer environments"; exact incident count not found | 2025 edition (updated Oct 2025), repeated in 2026 edition | https://montecarlo.ai/blog-data-quality-statistics and https://www.montecarlodata.com/blog-data-quality-statistics/ | search snippet only |
| Root cause | Pipeline execution faults 26.2% of data quality incidents. | DataMagnet playbook citing Monte Carlo | Monte Carlo (vendor), secondary citation | Same as above | 2026 | https://www.datamagnet.co/post/handle-data-quality-incidents/ | search snippet only (third-party citation) |
| Upstream changes | "Thirty-one percent of respondents told us that upstream changes are the most common data quality issue they face." Also: 20% had at least 2 severe incidents in 6 months. | Dataversity article by Kyle Kirwan | Bigeye (vendor; author is a Bigeye co-founder, article promotes a monitoring product) | 100 (at least 63 from large cloud warehouse customers) | Year not shown in snippet | https://www.dataversity.net/articles/which-data-quality-issues-are-plaguing-data-engineers-today/ | search snippet only |
| Found by business | 74% say business stakeholders identify issues first "all or most of the time", up from 47% in 2022. | Monte Carlo, State of Data Quality 2023 | Wakefield Research for Monte Carlo (vendor) | 200 data professionals (March 2023) | 2023 | https://www.businesswire.com/news/home/20230502005377/en/Data-Downtime-Nearly-Doubled-Year-Over-Year-Monte-Carlo-Survey-Says | search snippet only |
| Time to detect | 68% report average time to detect of 4 hours or more, up from 62% in 2022. | Monte Carlo, State of Data Quality 2023 | Wakefield Research for Monte Carlo (vendor) | 200 | 2023 | https://tdwi.org/articles/2023/05/04/data-downtime-nearly-doubled-survey.aspx | search snippet only |
| Time to resolve | "Average time to resolution for a data incident has gone from nine hours to 15 hours year over year" (a 166% rise). 63% typically take 4 hours or more, up from 47%. | Monte Carlo, State of Data Quality 2023 | Wakefield Research for Monte Carlo (vendor) | 200 (2022 base: 300+) | 2023 | https://venturebeat.com/data-infrastructure/data-downtime-almost-doubles-as-professionals-struggle-with-quality-issues-survey-finds/ | search snippet only |
| Incident volume | Monthly data incidents per organization rose from 59 (2022) to 67 (2023). | Monte Carlo, State of Data Quality 2023 | Wakefield Research for Monte Carlo (vendor) | 200 | 2023 | https://www.businesswire.com/news/home/20230502005377/en | search snippet only |
| Time to detect | "70% of data leaders say data incidents take longer than 4 hours to detect." Two-thirds had an incident costing $100,000 or more in 6 months. | Monte Carlo, 2024 State of Reliable AI | Wakefield Research for Monte Carlo (vendor) | 200 US data engineers (Apr 24 to May 7, 2024) | 2024 | https://info.montecarlodata.com/hubfs/Assets%20-%20Guides%2c%20Ebooks%2c%20Reports/Wakefield%20Report%20-%20State%20of%20Reliable%20AI%20Survey%202024.pdf | search snippet only |
| Detection gap | 61% say that in their incidents, monitored metrics looked normal while a critical issue was happening. | Monte Carlo, State of AI Reliability (2026) | Monte Carlo (vendor) | Not found | 2026 | https://www.montecarlodata.com/state-of-ai-reliability | search snippet only |
| Data quality | 53% report poor data quality as a top challenge (2026). Over 56% cited poor data as a significant challenge (2025). | dbt Labs, State of Analytics Engineering 2026 and 2025 | dbt Labs (vendor) | 363 (2026); 459 (2025, survey Oct 8 to Dec 27, 2024) | 2025, 2026 | https://www.getdbt.com/resources/state-of-analytics-engineering-2026 and https://www.getdbt.com/resources/analysts-guide-to-working-with-data-engineering | search snippet only |
| Data contracts | "61% of surveyed organizations report using data contracts operationally, either across multiple domains or within specific projects." Data products 69% in 2026, up from 48% in 2024. | BARC, "Data Products and Data Contracts" study | BARC (analyst firm), sponsored by Actian (vendor) | 308 (November 2025) | 2026 | https://barc.com/research/data-products-contracts-2026/ and https://www.actian.com/lp/data-products-and-data-contracts-the-foundation-for-ai-success/ | search snippet only |

## Gaps

- No exact 2025 dbt figure for ambiguous data ownership. The 2026 report calls 41% "effectively unchanged year over year".
- No exact decimal for dbt 2024 ("almost 50%").
- No independent (non-vendor) root-cause breakdown of data incidents was found.
- Time to resolve after 2023: the 2024 Monte Carlo report has a "Time to resolution" section, but its numbers did not appear in search results.
- Not searched in depth for lack of time: Precisely/Drexel, DataKitchen, Ataccama, GX, Atlan, Starburst, Fivetran, Airbyte, Anomalo, Soda, Gartner.
