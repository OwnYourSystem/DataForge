# Infrastructure

Terraform for the DataForge lab platform. Decisions: [ADR-001](../docs/adr/001-terraform.md)
and [ADR-004](../docs/adr/004-run-isolation.md).

**Status:** this code has passed `terraform fmt`, and CI runs
`terraform validate`. It has not been planned or applied against a
subscription.

## What `azure-dev` creates

| Resource | Purpose |
|---|---|
| Resource group and Databricks workspace (Premium) | The lab workspace |
| Storage account, access connector, storage credential, external location | Storage for the lab catalog |
| Catalog `dataforge_lab` and its grants | One schema for each lesson run |
| 1 platform principal, 1 learner principal for each worker, OAuth secrets | Identities (ADR-004) |
| Serverless SQL warehouse, size 2X-Small, 1 cluster, auto-stop 5 minutes | Runs the SQL |

## One-time manual steps

Terraform cannot do these. Rule 5 of the platform track wants each one
written down as a gap.

1. **An Azure subscription.** Use a personal subscription. Your user needs
   Owner on it, or Contributor plus User Access Administrator, because the
   code makes a role assignment.
2. **State storage.**

```bash
terraform -chdir=infra/bootstrap/azure-state init
```

```bash
terraform -chdir=infra/bootstrap/azure-state apply -var subscription_id=<your subscription id>
```

   Give your user the role **Storage Blob Data Contributor** on the new
   storage account. Copy the output values to
   `infra/envs/azure-dev/backend.hcl` (see `backend.hcl.example`).
3. **For CI only:** an Entra application with a federated credential for this
   repository, with the same roles as in steps 1 and 2. Then set the
   repository variables that `.github/workflows/infra-azure-dev.yml` names,
   and add reviewers to the GitHub environment `azure-dev`.

## Apply from your computer

```bash
az login
```

```bash
cp infra/envs/azure-dev/terraform.tfvars.example infra/envs/azure-dev/terraform.tfvars
```

```bash
terraform -chdir=infra/envs/azure-dev init -backend-config=backend.hcl
```

```bash
terraform -chdir=infra/envs/azure-dev apply
```

The outputs are the `DF_DBX_*` settings of the worker. To read a secret:

```bash
terraform -chdir=infra/envs/azure-dev output -raw df_dbx_platform_client_secret
```

## Remove everything

```bash
terraform -chdir=infra/envs/azure-dev destroy
```

The state storage from the bootstrap stays. It costs almost nothing. Remove
it with `destroy` in `infra/bootstrap/azure-state` when you stop the project.

## Cost

The warehouse is the only part with a real cost, and only while it runs. It
stops after 5 minutes with no query. A workspace with a stopped warehouse
costs nothing for compute. Storage for the catalog holds a few kilobytes.
Run `destroy` after a test if you do not need the environment.
