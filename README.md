# DataForge

**Know who you will break before you merge.**

DataForge finds changes that cross an ownership boundary on a data platform,
before they break data that another team depends on. It reads metadata from
Terraform, Azure, Databricks Unity Catalog, and dbt, joins it into 1 graph
with an owner on each node, and tells the owners on the other side of a
change, in the pull request.

DataForge reads metadata only. It never reads rows of data, and it never
writes to the platform that it reads.

- **Overview (start here):** [docs/overview.md](docs/overview.md)
- Decision to change direction: [docs/adr/005-change-impact-tool.md](docs/adr/005-change-impact-tool.md)
- Desk research method and gate: [docs/research/method.md](docs/research/method.md)
- Reference platform (Terraform): [infra/README.md](infra/README.md)

## Status

| Area | State |
|---|---|
| Reference platform on Azure (Terraform) | Written and validated. **Not applied** |
| Desk research on boundary incidents | **Not started** |
| Collectors, graph, impact engine | **Not started** |
| Learning portal | **Archived.** See below |

The full status and roadmap are in [docs/overview.md](docs/overview.md).

## Repository layout

| Path | Contents | State |
|---|---|---|
| `infra/` | Terraform: the reference platform on Azure Databricks | Active |
| `docs/` | Overview, ADRs, research, threat model | Active |
| `apps/api/` | API, database layer, worker queue | Active, to be reused for the graph store |
| `apps/web/` | Web portal with the lab editor | Archived |
| `curriculum/` | LAB-001 | Archived demo |
| `deploy/`, `render.yaml` | The portal deployment on Render | Archived, to be removed |

## The archived learning portal

The first version of DataForge was a learning portal with a hands-on dbt
lab. That direction stopped on 19 November 2026. The code stays in the
repository as a demo, and CI still tests it, but it is not developed.

- What it was: [docs/spec/learning-portal-overview.md](docs/spec/learning-portal-overview.md)
- Original specification: [docs/spec/dataforge-v1.0-original.md](docs/spec/dataforge-v1.0-original.md)
- Decisions in the first version: [docs/spec/fast-path.md](docs/spec/fast-path.md)

To run the archived lab on your computer:

```bash
docker compose up --build
```

Open http://localhost:3000, type a name, and select **Build and test**.

## Tests

```bash
cd apps/api && .venv/bin/pytest -q
```
