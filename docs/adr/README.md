# Architecture decision records

One short file for each important decision. A record is not changed after it
is accepted. A new record replaces it.

| Number | Decision | Status |
|---|---|---|
| [001](001-terraform.md) | Terraform for infrastructure: state, modules, and the manual bootstrap | Accepted |
| 002 | Not used. Was reserved for cross-project dbt references | Not used |
| 003 | Not used. Was reserved for Azure and AWS | Not used |
| [004](004-run-isolation.md) | Two kinds of service principal for run isolation | Accepted. Replaced in part by 005 |
| [005](005-change-impact-tool.md) | From learning portal to change-impact tool | Accepted |

Decisions before these records are in [../spec/fast-path.md](../spec/fast-path.md).
