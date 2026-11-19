# ADR-001: Terraform for infrastructure

Date: 15 November 2026
Status: accepted

## Context

Phase 1 of the platform track needs the Databricks lab on Azure as code.
`terraform apply` must give a working environment, and `terraform destroy`
must remove all of it. Phase 3 needs the same on AWS.

## Decision

**Tool.** Terraform, with the `azurerm` and `databricks` providers. Both
clouds and Databricks have maintained providers, and Terraform is the tool
that most platform teams use. Bicep was not selected because it does not
manage Databricks or AWS.

**Layout.**

```text
infra/
  bootstrap/azure-state/   state storage, applied one time with local state
  modules/                 one module for each part, no environment values
  envs/azure-dev/          one root module for each environment
```

**Module boundaries.** A module holds one thing that has one owner and one
reason to change:

| Module | Contents | Cloud-specific? |
|---|---|---|
| `databricks-workspace` | Resource group and workspace | Yes (Azure) |
| `unity-catalog` | Catalog, its storage, and the catalog grants | Storage part is Azure |
| `service-principals` | Platform and learner principals, and their secrets | No |
| `sql-warehouse` | Serverless warehouse and its permissions | No |

Modules take application ids as inputs. They do not look up each other.
The environment root module connects them.

**State.** Azure Blob Storage, one state file for each environment, with the
blob lease as the lock. The storage account has no access keys: Terraform
uses Microsoft Entra sign-in. Blob versions are on, with 30 days of soft
delete.

**Workloads are not in Terraform.** Run schemas are made and dropped by the
platform principal at run time. Jobs that run dbt will use Databricks Asset
Bundles in Phase 2. Terraform owns only the things that live as long as the
environment.

**CI.** Format and validate on each push. Plan on a pull request that changes
`infra/`. Apply and destroy only from a manual workflow, with approval on the
GitHub environment `azure-dev`. CI signs in with GitHub OIDC, so no cloud
secret is stored in GitHub.

## Consequences

- **The state holds secrets.** The OAuth secrets of the service principals are
  in the state file. This is the reason for the private state storage.
- **A manual bootstrap stays.** Terraform cannot create these, and rule 5 of
  the platform track needs them written down. See `infra/README.md`:
  1. The Azure subscription.
  2. The Entra application for CI, with its federated credential.
  3. The state storage (as code, but applied by a person one time).
  4. The reviewers on the GitHub environment `azure-dev`.
- **The workspace must have Unity Catalog.** New Azure workspaces get a
  metastore automatically in most regions. If a region does not do this, an
  account admin must assign a metastore first.
- **The Databricks provider is configured from a resource in the same
  apply** (the workspace). This normally works. If a first apply fails for
  this reason, apply the workspace module first with `-target`.

## Not yet proven

This code has passed `terraform fmt`. It has not been planned or applied
against a subscription. Phase 1 is done only when the acceptance criteria
in `docs/spec/platform-proof-track.md` pass.
