# Infrastructure

Terraform for the DataForge lab platform. Decisions: [ADR-001](../docs/adr/001-terraform.md)
and [ADR-004](../docs/adr/004-run-isolation.md).

**Status:** this code has passed `terraform fmt` and `terraform validate`
in CI. It has not been planned or applied against a subscription. The steps
below are not yet tested end to end.

## What `azure-dev` creates

| Resource | Purpose |
|---|---|
| Resource group and Databricks workspace (Premium) | The lab workspace |
| Storage account, access connector, storage credential, external location | Storage for the lab catalog |
| Catalog `dataforge_lab` and its grants | One schema for each lesson run |
| 1 platform principal, 1 learner principal for each worker, OAuth secrets | Identities (ADR-004) |
| Serverless SQL warehouse, size 2X-Small, 1 cluster, auto-stop 5 minutes | Runs the SQL |

## Before you start

- **An Azure subscription with billing on.** Use a personal pay-as-you-go
  subscription. Serverless SQL warehouses may not be available on a
  free-trial subscription: this is not verified.
- **Owner on that subscription**, or Contributor plus User Access
  Administrator. The code makes a role assignment.
- **Somewhere to run the commands:** Azure Cloud Shell (no computer needed)
  or your own computer with `az`, `git` and Terraform 1.9 or later.

## Manual gaps

Terraform cannot do these. Rule 5 of the platform track wants each one
written down as a gap.

| Gap | Where |
|---|---|
| The Azure subscription and its billing | Azure portal |
| The state storage: as code, but applied by a person one time | Steps 3 and 4 below |
| Your data role on the state storage | Step 4 below |
| The repository secrets for the live test | Step 7 below |
| For CI apply only: an Entra application with a federated credential for this repository, the repository variables that `.github/workflows/infra-azure-dev.yml` names, and reviewers on the GitHub environment `azure-dev` | Not needed for the first proof |

## Apply with Azure Cloud Shell

Cloud Shell runs in a browser. It has `az`, `git`, `jq` and `terraform`, and
you are signed in to Azure. It works on a phone, with a small screen.

Time: about 30 minutes, plus 10 to 15 minutes of waiting for Azure.

### 1. Open Cloud Shell

Open shell.azure.com and choose **Bash**. Check the subscription:

```bash
az account show --query "{name:name, id:id}" -o table
```

If it is the wrong subscription, change it:

```bash
az account set --subscription "<subscription id>"
```

Keep the id in a variable for the next steps:

```bash
SUB=$(az account show --query id -o tsv)
```

### 2. Get the code

Clone the branch that has `infra/`. Until pull request 3 is merged, that is
`claude/dataforge-automated-build-k2ywbu`. After the merge, use `main`.

```bash
git clone --branch claude/dataforge-automated-build-k2ywbu https://github.com/OwnYourSystem/DataForge.git
```

```bash
cd DataForge
```

If the repository is private, git asks for a user name and a password. Give
your GitHub user name, and a GitHub personal access token as the password.

### 3. Create the state storage

This root module keeps its own state on the Cloud Shell disk.

```bash
terraform -chdir=infra/bootstrap/azure-state init
```

```bash
terraform -chdir=infra/bootstrap/azure-state apply -var subscription_id=$SUB
```

Type `yes`. The output `backend_config` shows 3 names. Copy the storage
account name: it starts with `stdataforgetf`.

### 4. Give yourself a data role on the state storage

The storage account has no access keys, so your user needs a data role:

```bash
SA=<the storage account name from step 3>
```

```bash
az role assignment create --assignee $(az ad signed-in-user show --query id -o tsv) --role "Storage Blob Data Contributor" --scope $(az storage account show -n $SA -g rg-dataforge-tfstate --query id -o tsv)
```

Wait about 5 minutes. A new role assignment takes time to take effect, and
step 6 fails with HTTP 403 until it does.

### 5. Configure the environment

```bash
cd infra/envs/azure-dev
```

```bash
printf 'resource_group_name  = "rg-dataforge-tfstate"\nstorage_account_name = "%s"\ncontainer_name       = "tfstate"\n' $SA > backend.hcl
```

```bash
printf 'subscription_id = "%s"\n' $SUB > terraform.tfvars
```

Both files are in `.gitignore`.

### 6. Create the lab platform

```bash
terraform init -backend-config=backend.hcl
```

```bash
terraform plan -out lab.tfplan
```

Read the plan. Expect about 20 resources to add and 0 to destroy.

```bash
terraform apply lab.tfplan
```

This takes about 10 to 15 minutes. The workspace takes most of the time.

If the apply stops with a Databricks error about the host or about
authentication, the workspace was not ready when the Databricks provider
started. Create the workspace first, then run the plan and the apply again:

```bash
terraform apply -target=module.workspace
```

### 7. Run the live test

The live test runs the lesson on the real workspace. It also checks that the
learner identity cannot read a different run.

Add these 7 repository secrets on GitHub: Settings, Secrets and variables,
Actions, New repository secret. Read each value in Cloud Shell, and paste it
only into GitHub.

| Secret | Command that shows the value |
|---|---|
| `DF_DBX_HOST` | `terraform output -raw df_dbx_host` |
| `DF_DBX_HTTP_PATH` | `terraform output -raw df_dbx_http_path` |
| `DF_DBX_CATALOG` | `terraform output -raw df_dbx_catalog` |
| `DF_DBX_PLATFORM_CLIENT_ID` | `terraform output -raw df_dbx_platform_client_id` |
| `DF_DBX_PLATFORM_CLIENT_SECRET` | `terraform output -raw df_dbx_platform_client_secret` |
| `DF_DBX_LEARNER_CLIENT_ID` | `terraform output -json df_dbx_learner_client_ids \| jq -r '.[0]'` |
| `DF_DBX_LEARNER_CLIENT_SECRET` | `terraform output -json df_dbx_learner_client_secrets \| jq -r '.[0]'` |

Then open the Actions tab, select **Databricks live test**, select **Run
workflow**, and choose the branch from step 2. Until pull request 3 is
merged, `main` has the old secret names, and a run on `main` fails.

### 8. Remove everything after the test

```bash
terraform destroy
```

Type `yes`. The state storage from step 3 stays (see below).

## Apply from your computer

The same steps as in Cloud Shell, with 2 differences:

1. Sign in first:

```bash
az login
```

2. Run the commands from a clone of the repository. Steps 2 to 8 are the
   same.

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
