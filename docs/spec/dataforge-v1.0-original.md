# DataForge

**Hybrid Data Engineering Academy & Workbench — Azure Proof-of-Concept Specification**  
**Version:** 1.0  
**Date:** 10 November 2026  
**Status:** Proposed architecture; not yet deployed or validated

## 1. Executive recommendation

Build a browser-based, guided data engineering learning platform for individual engineers. Learners should be able to launch managed sandboxes, write and execute code, receive automated validation, and preserve their work without configuring a local development environment.

The first proof of concept (POC) must demonstrate one end-to-end Databricks + dbt lesson, with secure provisioning, execution, grading, metering, persistence, and cleanup. Use a **hybrid managed sandbox** model:

- **Tier A — Shared learning:** Restricted SQL and dbt exercises on shared Azure Databricks infrastructure, with learner-scoped data and execution identities.
- **Tier B — Dedicated advanced learning:** Strongly isolated Azure resources and a dedicated Databricks workspace for approved Terraform and deployment labs.

**Key principle:** Separate the learning **control plane** from the untrusted **execution plane**. Do not build a full academy before proving that one lab can run securely and economically.

## 2. POC scope and acceptance scenario

A learner must be able to:

1. Register and sign in to the portal.
2. Launch a preconfigured managed sandbox.
3. Open a guided lesson with an embedded editor.
4. Load a synthetic retail customer dataset into Delta Lake.
5. Implement a dbt staging model and data-quality tests.
6. Execute dbt through a restricted backend operation.
7. Inspect sanitized logs and receive independent automated grading.
8. End the session, release compute, and resume saved project work.

An administrator-controlled Tier B experiment must additionally provision, validate, and destroy a dedicated Terraform lab. Public learners will not have unrestricted infrastructure provisioning in the POC.

### Explicitly out of scope

General-purpose user dataset uploads, unrestricted shell access, arbitrary Terraform providers/modules, AI tutoring, payment subscriptions, enterprise classrooms, eBook publishing, and public production launch.

## 3. Azure architecture

### Logical topology

```text
Learner Browser
  └── Next.js Portal + Monaco Editor
       └── FastAPI Control Plane
            ├── Identity / Curriculum / Progress / Assessment / Quotas
            ├── PostgreSQL Flexible Server (application state)
            ├── Azure Blob Storage (project snapshots, datasets, artifacts)
            ├── Azure Key Vault (secrets)
            ├── Azure Service Bus (execution requests)
            ├── Azure Monitor / Application Insights (telemetry)
            └── Durable Sandbox Orchestrator
                 ├── Tier A: restricted ephemeral worker
                 │    └── shared Azure Databricks + learner-scoped resources
                 └── Tier B: dedicated execution environment
                      └── isolated Azure subscription + Databricks workspace
```

### Azure services

| Service | Purpose | POC recommendation |
|---|---|---|
| Azure Container Apps | Web and API hosting | Separate services |
| Azure Container Apps Jobs | Ephemeral dbt workers | One bounded job per execution |
| Azure Container Registry | Trusted worker images | Private registry |
| Azure Database for PostgreSQL Flexible Server | Application data | Private where feasible |
| Azure Blob Storage | Files, datasets, logs, snapshots | Private containers and lifecycle rules |
| Azure Key Vault | Secrets | RBAC and managed identity |
| Azure Service Bus | Async execution messages | Dead-letter queue |
| Azure Databricks | SQL/Delta/dbt labs | Shared Tier A workspace |
| Azure Monitor / Application Insights | Logs, traces, metrics | Correlation IDs |
| Microsoft Entra External ID | Customer authentication | OIDC |
| Azure Cost Management | Budgets and reporting | Alerts plus app-level hard quotas |

### Subscription boundaries

```text
Azure Tenant
├── academy-platform-dev
│   ├── rg-academy-app
│   ├── rg-academy-data
│   ├── rg-academy-security
│   └── rg-academy-observability
├── academy-shared-labs
│   ├── rg-databricks-shared
│   ├── rg-lab-storage
│   └── rg-lab-execution
└── academy-dedicated-pool
    └── pre-created isolated sandbox subscription(s) for the POC
```

Subscription names are illustrative. A dedicated subscription is preferable for advanced labs that can modify cloud resources. Begin with one pre-created dedicated sandbox subscription instead of automating subscription vending in the first POC.

## 4. Technology choices

| Layer | Recommendation |
|---|---|
| Frontend | Next.js, React, TypeScript, Monaco Editor |
| API | Python FastAPI, OpenAPI 3.1 |
| Database | PostgreSQL, migration tooling |
| Durable orchestration | Durable workflow engine / managed equivalent |
| Worker | Ephemeral restricted container job |
| Data execution | Azure Databricks SQL, Delta Lake |
| Transformations | dbt-databricks |
| Infrastructure | Terraform, separate state per environment/sandbox |
| CI/CD | GitHub Actions with workload identity federation |
| Monitoring | OpenTelemetry, Azure Monitor, Application Insights |

Use a modular monolith for the initial application. Split services only where execution isolation or independent scaling requires it.

## 5. Terraform module structure

```text
infrastructure/terraform/
├── bootstrap/backend/
├── modules/
│   ├── resource-group/
│   ├── networking/
│   ├── container-apps/
│   ├── postgres/
│   ├── storage/
│   ├── key-vault/
│   ├── service-bus/
│   ├── databricks-workspace/
│   ├── databricks-identity/
│   └── lab-compute/
└── environments/
    ├── platform-dev/
    ├── shared-labs/
    └── dedicated-lab/
```

Bootstrap the Terraform Azure Storage backend first. Use separate root modules and state for platform, shared lab, and each dedicated sandbox. Use Microsoft Entra authentication, blob versioning, storage protection, and restricted access.

### Example Terraform root

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "rg-academy-tfstate"
    storage_account_name = "academyterraformstate"
    container_name       = "tfstate"
    key                  = "platform-dev.tfstate"
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
```

The storage account name must be replaced with a globally unique available name. Provider constraints are illustrative; verify and pin tested versions and commit `.terraform.lock.hcl`. Deploy Azure resources before configuring Databricks workspace resources through a separate Terraform root.

### Example module invocation

```hcl
module "shared_databricks" {
  source = "../../modules/databricks-workspace"

  resource_group_name = module.resource_group.name
  location            = var.location
  workspace_name      = var.workspace_name

  tags = {
    environment = "poc"
    workload    = "academy-shared-labs"
    managed_by  = "terraform"
  }
}
```

## 6. Security design

### Trust boundaries

1. **Browser:** Authenticated interface only. Never exposes cloud, Databricks admin, Terraform state, or grading credentials.
2. **Control plane:** Authoritative user ownership, entitlements, operation validation, quota reservation, and audit.
3. **Execution plane:** Ephemeral workers, constrained commands, non-privileged containers, timeouts, restricted egress.
4. **Cloud/Databricks:** Scoped identities, policy restrictions, dedicated resource boundaries where required.

### Identities

| Identity | Permission scope |
|---|---|
| API managed identity | Application storage, queues, permitted vault secrets |
| Provisioner identity | Allowlisted lab resource creation and destruction |
| Learner execution identity | Only assigned lab resources and approved operations |
| Assessment identity | Independent read-only access to required outputs |

### Tier A requirements

- Learner-specific catalog/schema or similarly scoped Unity Catalog namespace and storage prefix.
- Independently authorized execution; avoid a single broadly privileged shared identity.
- No cluster, workspace identity, external location, or cloud resource administration.
- Controlled SQL/dbt operations; no arbitrary shell or Python execution.
- Compute limits, timeouts, session quotas, and sanitized logs.
- Explicit isolation tests: shared schemas alone do **not** make arbitrary code safe.

### Tier B requirements

- Dedicated subscription or equivalent strong boundary; dedicated Databricks workspace for infrastructure labs.
- Separate Terraform state, provider identity, resource inventory, and TTL.
- Azure Policy restrictions, resource type allowlists, capacity limits, and denied privilege escalation.
- Approved Terraform workflow: `fmt -check` → `validate` → policy checks → `plan` → controlled `apply`.
- Independent expiration and resource cleanup, even if the learner disconnects.

### Threat tests

- Learner A tries to read Learner B's files or tables.
- Code attempts to retrieve platform secrets or metadata.
- Terraform attempts to create unauthorized resources or elevate privileges.
- Learner attempts to forge grading or completion records.
- Repeated jobs attempt to exhaust budgets.
- Provisioning fails halfway and leaves resources behind.
- A malicious file attempts to exploit the parser or execution environment.

## 7. Data model

Use PostgreSQL for application state, not Databricks. Core tables:

| Domain | Tables |
|---|---|
| Identity | `users`, `user_roles` |
| Curriculum | `learning_paths`, `modules`, `lessons`, `lesson_versions` |
| Progress | `enrollments`, `lesson_progress` |
| Projects | `projects`, `project_files`, `project_snapshots` |
| Sandboxes | `sandbox_templates`, `sandboxes`, `sandbox_resources` |
| Execution | `executions`, `execution_artifacts` |
| Grading | `validation_rules`, `assessments`, `assessment_results` |
| Cost | `usage_events`, `quota_policies`, `usage_ledger` |
| Operations | `workflow_operations`, `audit_events`, `outbox_events` |

Use UUIDs, UTC timestamps, foreign keys, versioned lessons, ownership checks, indexed lifecycle queries, immutable usage events, and transactional idempotency. Prevent duplicate chargeable sandbox allocation with transactionally enforced active-sandbox quotas.

### Starter DDL

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE sandbox_tier AS ENUM ('shared', 'dedicated');
CREATE TYPE sandbox_status AS ENUM (
  'requested', 'provisioning', 'ready', 'running',
  'suspending', 'suspended', 'destroying', 'destroyed', 'failed'
);
CREATE TYPE execution_status AS ENUM (
  'queued', 'running', 'succeeded', 'failed', 'cancelled', 'timed_out'
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  identity_subject TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL,
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE learning_paths (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  published_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  learning_path_id UUID NOT NULL REFERENCES learning_paths(id),
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  UNIQUE (learning_path_id, position)
);

CREATE TABLE lessons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID NOT NULL REFERENCES modules(id),
  slug TEXT NOT NULL,
  title TEXT NOT NULL,
  position INTEGER NOT NULL,
  UNIQUE (module_id, slug),
  UNIQUE (module_id, position)
);

CREATE TABLE lesson_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_id UUID NOT NULL REFERENCES lessons(id),
  version INTEGER NOT NULL,
  content_uri TEXT NOT NULL,
  template_digest TEXT NOT NULL,
  published_at TIMESTAMPTZ,
  UNIQUE (lesson_id, version)
);

CREATE TABLE enrollments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  learning_path_id UUID NOT NULL REFERENCES learning_paths(id),
  enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, learning_path_id)
);

CREATE TABLE lesson_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  enrollment_id UUID NOT NULL REFERENCES enrollments(id),
  lesson_version_id UUID NOT NULL REFERENCES lesson_versions(id),
  status TEXT NOT NULL DEFAULT 'not_started'
    CHECK (status IN ('not_started', 'in_progress', 'completed')),
  completed_at TIMESTAMPTZ,
  UNIQUE (enrollment_id, lesson_version_id)
);

CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  storage_prefix TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sandboxes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  project_id UUID NOT NULL REFERENCES projects(id),
  tier sandbox_tier NOT NULL,
  status sandbox_status NOT NULL DEFAULT 'requested',
  template_version TEXT NOT NULL,
  cloud_resource_id TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  destroyed_at TIMESTAMPTZ,
  UNIQUE (id, user_id)
);

CREATE TABLE executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sandbox_id UUID NOT NULL REFERENCES sandboxes(id),
  user_id UUID NOT NULL REFERENCES users(id),
  lesson_version_id UUID REFERENCES lesson_versions(id),
  operation TEXT NOT NULL,
  status execution_status NOT NULL DEFAULT 'queued',
  request_hash TEXT NOT NULL,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  result_uri TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY (sandbox_id, user_id) REFERENCES sandboxes(id, user_id)
);

CREATE INDEX idx_sandboxes_owner_status ON sandboxes(user_id, status);
CREATE INDEX idx_executions_sandbox_created
  ON executions(sandbox_id, created_at DESC);
```

This is starter DDL, not a complete production migration. Add composite project-owner integrity, validation and assessment tables, resource inventory, outbox events, quotas, and lifecycle transition enforcement before production.

## 8. Sandbox lifecycle

```text
REQUESTED → PROVISIONING → READY ⇄ RUNNING
                          │
                          └→ SUSPENDING → SUSPENDED → RESUME
Any active state → DESTROYING → DESTROYED
Operational failure → FAILED → recovery / cleanup workflow
```

### Provision

1. Authenticate and authorize learner.
2. Resolve lesson to a server-owned sandbox template and tier.
3. Check and reserve quota; apply idempotency key.
4. Create sandbox and durable workflow records transactionally.
5. Allocate restricted resources through Tier A/B provider.
6. Inject short-lived credentials into isolated worker.
7. Health-check identity, data access, and execution readiness.
8. Transition to `ready` and emit status event.

### Execute

1. Accept a predefined operation identifier and schema-validated arguments.
2. Confirm sandbox ownership, state, entitlement, and remaining quota.
3. Queue bounded execution with correlation ID.
4. Run trusted handler; stream sanitized events.
5. Evaluate output in a separate trusted grading context.
6. Persist results and usage events; return sandbox to `ready`.

### Suspend and destroy

- Preserve project files before stopping workers.
- Terminate compute after idle timeout; do not confuse sandbox wall-clock time with billable compute.
- Expire dedicated resources independently of browser connectivity.
- Make deletion idempotent and verify actual cloud resource removal.
- Reconcile database records against Azure/Databricks inventory and retry orphan cleanup.

## 9. API contracts

All endpoints require authentication and server-side ownership checks. Use OpenAPI 3.1, `202 Accepted` for asynchronous work, `Idempotency-Key` for provisioning/chargeable actions, and SSE for execution events.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/me` | User and entitlements |
| GET | `/v1/learning-paths` | Available learning paths |
| GET | `/v1/lessons/{id}` | Lesson manifest and instructions |
| POST | `/v1/enrollments` | Enroll |
| POST | `/v1/projects` | Create project |
| GET | `/v1/projects/{id}/files` | List project files |
| PUT | `/v1/projects/{id}/files/{path}` | Save file; prevent path traversal |
| POST | `/v1/sandboxes` | Request sandbox |
| GET | `/v1/sandboxes/{id}` | Read sandbox state |
| POST | `/v1/sandboxes/{id}/resume` | Resume |
| DELETE | `/v1/sandboxes/{id}` | Request destruction |
| POST | `/v1/sandboxes/{id}/executions` | Run approved operation |
| GET | `/v1/executions/{id}` | Result/status |
| GET | `/v1/executions/{id}/events` | SSE logs/status |
| POST | `/v1/executions/{id}/cancel` | Cancel |
| POST | `/v1/assessments` | Request grading |
| GET | `/v1/assessments/{id}` | Read grading |
| GET | `/v1/usage` | Quota and usage |

### Create sandbox

```http
POST /v1/sandboxes
Idempotency-Key: 9cdbf8bc-example
Content-Type: application/json
```

```json
{
  "project_id": "bca2c5f3-8341-40de-9c7c-318dba50ab2d",
  "lesson_id": "retail-dbt-001"
}
```

```json
{
  "sandbox_id": "f4b72514-5a3c-4c9e-a36d-fde0bbdf08fa",
  "operation_id": "8b291e57-ff18-471d-b8c0-8d3b5c9172e1",
  "status": "provisioning",
  "status_url": "/v1/sandboxes/f4b72514-5a3c-4c9e-a36d-fde0bbdf08fa"
}
```

### Run a dbt exercise

```json
{
  "operation_id": "dbt_build",
  "arguments": {"select": "stg_customers"}
}
```

The executor maps `dbt_build` to a trusted handler; it must never concatenate untrusted strings into a shell command.

### Assessment result example

```json
{
  "execution_id": "7f6a1c35-fc50-4979-9187-27c879eac11a",
  "status": "succeeded",
  "assessment": {
    "passed": true,
    "score": 100,
    "checks": [
      {"id": "dbt-build", "passed": true},
      {"id": "unique-customer-key", "passed": true},
      {"id": "not-null-customer-key", "passed": true}
    ]
  }
}
```

Return consistent problem responses for quota exhaustion, unauthorized access, invalid state, and provisioning failure. Enforce request limits and correlation IDs.

## 10. First executable lesson — LAB-001

**Title:** Build and Test a Retail Customer Staging Model  
**Level:** Beginner  
**Duration:** 45–60 minutes  
**Tier:** A (shared, restricted)  
**Tools:** Azure Databricks SQL, Delta Lake, dbt-databricks

### Learning objectives

- Load synthetic raw customer records.
- Reference a dbt source.
- Create a staging model with standardized columns.
- Run dbt tests.
- Diagnose failures and validate results.

### Lab file layout

```text
retail-lakehouse/
├── dbt_project.yml
├── profiles.yml
├── seeds/raw_customers.csv
├── models/staging/_sources.yml
├── models/staging/_staging.yml
├── models/staging/stg_customers.sql
└── README.md
```

#### `seeds/raw_customers.csv`

```csv
customer_id,customer_name,email,country
1001,Alice Jensen,alice@example.com,Denmark
1002,Daniel Smith,daniel@example.com,United Kingdom
1003,Sara Nielsen,sara@example.com,Denmark
1004,Peter Hansen,peter@example.com,Norway
1005,Maria Lopez,maria@example.com,Spain
```

These records are fictional and intended for synthetic POC data.

#### `dbt_project.yml`

```yaml
name: retail_lakehouse
version: "1.0.0"
config-version: 2
profile: retail_lakehouse
model-paths: ["models"]
seed-paths: ["seeds"]
models:
  retail_lakehouse:
    staging:
      +materialized: table
```

#### `profiles.yml`

```yaml
retail_lakehouse:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: "{{ env_var('DBX_CATALOG') }}"
      schema: "{{ env_var('DBX_SCHEMA') }}"
      host: "{{ env_var('DBX_HOST') }}"
      http_path: "{{ env_var('DBX_HTTP_PATH') }}"
      token: "{{ env_var('DBX_TOKEN') }}"
      threads: 2
```

Inject a short-lived token at runtime; never commit it or expose it in logs. Prefer supported OAuth machine-to-machine authentication for production.

#### `models/staging/_sources.yml`

```yaml
version: 2
sources:
  - name: retail_raw
    catalog: "{{ env_var('DBX_CATALOG') }}"
    schema: "{{ env_var('DBX_SCHEMA') }}"
    tables:
      - name: raw_customers
```

#### `models/staging/stg_customers.sql` — reference solution

```sql
with source_data as (
    select
        customer_id,
        customer_name,
        email,
        country
    from {{ source('retail_raw', 'raw_customers') }}
),
cleaned as (
    select
        cast(customer_id as bigint) as customer_key,
        trim(customer_name) as customer_name,
        lower(trim(email)) as email,
        upper(trim(country)) as country,
        current_timestamp() as processed_at
    from source_data
)
select *
from cleaned
```

Give the learner an incomplete starter file. Keep this reference solution inaccessible to the learner's runtime and export.

#### `models/staging/_staging.yml`

```yaml
version: 2
models:
  - name: stg_customers
    description: Cleaned customer records
    columns:
      - name: customer_key
        description: Unique customer identifier
        data_tests:
          - unique
          - not_null
      - name: email
        data_tests:
          - not_null
```

### Trusted runner commands

```bash
dbt debug --profiles-dir .
dbt seed --profiles-dir .
dbt build --select stg_customers --profiles-dir .
```

Expected result: connection succeeds; seed creates `raw_customers`; model materializes and tests pass. This has **not** been executed against a real Databricks workspace in this specification.

### Independent grading SQL

```sql
SELECT
  COUNT(*) AS row_count,
  COUNT(DISTINCT customer_key) AS unique_customers,
  SUM(CASE WHEN customer_key IS NULL THEN 1 ELSE 0 END)
    AS null_customer_keys
FROM learner_catalog.learner_schema.stg_customers;
```

Replace the catalog/schema with the assigned namespace. For the synthetic seed, expected results are row count **5**, distinct keys **5**, null keys **0**. Also verify lowercase emails, uppercase countries, expected schema, and dbt test results.

### Assessment rubric

| Criterion | Weight |
|---|---:|
| Correct source reference | 15% |
| Correct transformations | 30% |
| Successful dbt build | 20% |
| Data-quality tests | 25% |
| Model structure and naming | 10% |
| **Total** | **100%** |

Passing threshold: **80%**, with all critical quality checks required.

## 11. Containerized dbt runner

### `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /workspace
RUN groupadd --gid 10001 runner \
 && useradd --uid 10001 --gid 10001 --create-home runner
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
USER 10001:10001
ENTRYPOINT ["dbt"]
```

### `requirements.txt`

```text
dbt-databricks>=1.9,<2.0
```

For deployment, replace the range with a tested exact version and lock transitive dependencies. Mount a writable learner workspace, enforce CPU/memory/time limits, restrict egress, and use trusted operation handlers rather than a general-purpose shell.

## 12. Curriculum-as-code manifest

```yaml
id: dbt-staging-customers
version: 1
title: Build a Customer Staging Model
module: dbt-modeling
sandbox:
  tier: shared
  template: dbt-sql-v1
  max_session_minutes: 60
objectives:
  - Create a staging model
  - Standardize column names
  - Pass dbt data quality tests
starter:
  repository_path: starter-project/dbt
operations:
  - id: run_dbt
    handler: dbt_build
    arguments:
      select: stg_customers
validation:
  suite: customers-staging-v1
  minimum_score: 80
completion:
  require_all_critical_checks: true
```

Lessons should be versioned and include prerequisites, objectives, explanations, starter files, approved operations, validation, hints, and completion conditions. This also creates a foundation for future companion eBooks.

## 13. Monorepo structure

```text
DataForge/
├── apps/
│   ├── web/
│   └── api/
├── services/
│   ├── orchestrator/
│   ├── executor/
│   ├── assessor/
│   ├── metering/
│   └── reconciler/
├── packages/
│   ├── contracts/
│   ├── database/
│   ├── sandbox-sdk/
│   ├── curriculum-sdk/
│   └── ui/
├── infrastructure/
│   ├── terraform/
│   ├── kubernetes/
│   └── policies/
├── sandbox-images/
│   ├── base/
│   ├── dbt-runner/
│   ├── terraform/
│   └── databricks/
├── curriculum/
│   └── retail-lakehouse/
│       ├── path.yaml
│       ├── lessons/
│       ├── starter/
│       ├── datasets/
│       └── validators/
├── contracts/openapi.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── isolation/
│   └── e2e/
├── docs/
│   ├── architecture/
│   ├── adr/
│   ├── security/
│   └── runbooks/
└── .github/workflows/
```

Reference solutions and grading secrets must not be bundled into learner-accessible containers or exported project repositories.

## 14. Quotas, costs, and metering

### Proposed starter limits

```yaml
plan: individual_starter
limits:
  concurrent_sandboxes: 1
  monthly_compute_minutes: 600
  max_session_minutes: 90
  idle_timeout_minutes: 15
  max_execution_minutes: 20
  max_upload_mb: 100
  max_project_storage_gb: 2
dedicated_sandbox:
  enabled: true
  max_lifetime_minutes: 120
  max_active_instances: 1
  require_capacity_reservation: true
enforcement:
  reject_on_quota_exceeded: true
  auto_suspend_on_idle: true
  cleanup_on_expiry: true
```

These are test assumptions, not validated plan limits. Meter active compute, cloud resources, storage, and platform overhead separately. Reserve expected quota before provisioning and reconcile actual consumption from cloud records. Enforce both learner-level and global budgets. Azure Cost Management alerts alone are not immediate hard stops; implement platform-side admission controls and independent cleanup.

## 15. Reliability and observability

Instrument every request with a correlation ID across API, queue, workflow, worker, Databricks execution, grading, and cleanup. Track:

- Sandbox startup latency (p50/p95) and success rate.
- Execution duration, retries, and failure categories.
- Assessment outcomes and lesson completion.
- Worker and Databricks utilization.
- Orphaned resources and cleanup time.
- Cost per successful lab and per active learner.
- Unauthorized access attempts and policy violations.

Maintain runbooks for stuck provisioning, failed deletion, service outages, credential rotation, quota reconciliation, and security incidents. Use a durable orchestration mechanism for multi-step provisioning and teardown rather than relying on fire-and-forget background tasks.

## 16. Six-week POC plan

| Week | Focus | Deliverables |
|---|---|---|
| 1 | Azure foundation | Terraform backend, core resources, shared Databricks, identities, monitoring |
| 2 | Sandbox execution | dbt image, learner namespace, controlled execution, timeout and cleanup |
| 3 | Learning application | Authentication, lesson UI, editor, project storage, sandbox APIs |
| 4 | Assessment | dbt execution, logs, independent grading, progress, reset/retry |
| 5 | Hybrid validation | Dedicated sandbox, approved Terraform apply/destroy, isolation tests |
| 6 | Pilot | 5–10 test learners, cost measurements, defect fixes, acceptance report |

This is an aggressive schedule for a small experienced team and depends on Azure/Databricks access and approvals.

### Implementation epics

1. **Platform foundation (P0):** Monorepo, CI/CD, identity, database, curriculum APIs.
2. **Sandbox orchestration (P0):** Templates, idempotent workflows, Tier A/B adapters, expiry, reconciliation.
3. **Workbench (P0):** Monaco, file persistence, execution requests, logs, reset/retry.
4. **Databricks integration (P0):** Scoped identities, SQL and dbt adapters, approved Terraform/Bundle workflows.
5. **Learning and assessment (P0):** Lesson manifest, independent grading, progress, flagship lab.
6. **Security and operations (P0):** Isolation, metering, quotas, observability, adversarial tests.
7. **Pilot improvements (P1):** Learner trials, usability, costs, basic repository export.

### POC acceptance gates

| Gate | Required evidence |
|---|---|
| Functional | Learner completes lab entirely in browser |
| Persistence | Files and progress survive worker termination |
| Isolation | No cross-learner data or file access |
| Security | Unauthorized operations rejected |
| Cost | Per-session resource usage recorded |
| Reliability | Provisioning retries do not duplicate resources |
| Cleanup | Expired cloud resources verified removed |
| Terraform | Dedicated lab applies and destroys approved resources |
| Assessment | Incorrect transformations fail independent grading |
| Operations | Correlated logs diagnose end-to-end failures |

## 17. Architecture decisions to record

- ADR-001: Azure-first architecture and portability.
- ADR-002: Shared versus dedicated Databricks isolation.
- ADR-003: Durable workflow engine selection.
- ADR-004: Project file persistence and snapshots.
- ADR-005: Terraform execution, state, and permissions.
- ADR-006: Databricks identity and authorization.
- ADR-007: Quota reservation and usage reconciliation.
- ADR-008: Curriculum versioning and grading compatibility.
- ADR-009: Worker runtime and network isolation.
- ADR-010: Dedicated subscription provisioning and teardown.

## 18. Next engineering action

Implement the **vertical slice** before the full product:

> Authenticate → allocate restricted sandbox → seed customer data → run dbt model → independently validate → save progress → meter usage → stop compute → verify cleanup.

Then validate the dedicated Terraform sandbox separately. Do not treat this document as evidence of deployment or security certification. Exact provider, adapter, and runtime versions must be verified and pinned in a real Azure Databricks environment before release.
