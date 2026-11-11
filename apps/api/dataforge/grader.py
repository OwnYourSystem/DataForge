"""Independent grading.

The grader does not trust the dbt exit code alone. It opens the result
database read-only and compares the table with values it calculates itself.
"""

import csv
import json
import logging
from pathlib import Path

from .backends import Backend, RunContext
from .curriculum import Lesson

log = logging.getLogger("dataforge.grader")


def _check(check_id: str, title: str, weight: int, passed: bool, critical: bool = False) -> dict:
    return {
        "id": check_id,
        "title": title,
        "weight": weight,
        "passed": bool(passed),
        "critical": critical,
    }


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def grade_lab_001(lesson: Lesson, backend: Backend, ctx: RunContext) -> list[dict]:
    workspace = ctx.workspace
    model_id = "model.retail_lakehouse.stg_customers"
    manifest = _read_json(workspace / "target" / "manifest.json")
    run_results = _read_json(workspace / "target" / "run_results.json")
    statuses = {r["unique_id"]: r["status"] for r in run_results.get("results", [])}

    depends_on = manifest.get("nodes", {}).get(model_id, {}).get("depends_on", {}).get("nodes", [])
    uses_source = "source.retail_lakehouse.retail_raw.raw_customers" in depends_on
    model_built = statuses.get(model_id) == "success"
    test_statuses = [s for uid, s in statuses.items() if uid.startswith("test.")]
    dbt_tests_pass = len(test_statuses) >= 3 and all(s == "pass" for s in test_statuses)

    with open(lesson.project_dir / "seeds" / "raw_customers.csv", newline="") as handle:
        seed = list(csv.DictReader(handle))
    expected = sorted(
        (
            int(row["customer_id"]),
            row["customer_name"].strip(),
            row["email"].strip().lower(),
            row["country"].strip().upper(),
        )
        for row in seed
    )

    columns: list[tuple[str, str]] = []
    rows: list[tuple] = []
    counts: tuple = (0, 0, 0)
    table = backend.relation(ctx, "stg_customers")
    try:
        with backend.grader_query(ctx) as query:
            columns = backend.columns(query, ctx, "stg_customers")
            counts = tuple(
                query(
                    "select count(*), count(distinct customer_key), "
                    f"sum(case when customer_key is null then 1 else 0 end) from {table}"
                )[0]
            )
            rows = sorted(
                (
                    tuple(r)
                    for r in query(
                        f"select customer_key, customer_name, email, country from {table}"
                    )
                ),
                key=repr,
            )
    except Exception as exc:
        # The table or a column is missing, or the engine is not available.
        # The checks below fail. The detail goes to the worker log only.
        log.info("grader query failed: %s", type(exc).__name__)

    names = [c[0] for c in columns]
    types = dict(columns)
    structure_ok = names == ["customer_key", "customer_name", "email", "country", "processed_at"]
    transformations_ok = (
        types.get("customer_key") == "BIGINT"
        and types.get("processed_at", "").startswith("TIMESTAMP")
        and rows == sorted(expected, key=repr)
    )
    quality_ok = dbt_tests_pass and counts == (len(seed), len(seed), 0)

    return [
        _check("source-reference", "The model reads the dbt source", 15, uses_source),
        _check(
            "transformations", "Columns have the correct values and types", 30, transformations_ok
        ),
        _check("dbt-build", "The dbt build is successful", 20, model_built, critical=True),
        _check(
            "data-quality",
            "Keys are unique and not null; dbt tests pass",
            25,
            quality_ok,
            critical=True,
        ),
        _check("structure", "Column names and order are correct", 10, structure_ok),
    ]


GRADERS = {"lab-001": grade_lab_001}


def grade(lesson: Lesson, backend: Backend, ctx: RunContext) -> dict:
    checks = GRADERS[lesson.id](lesson, backend, ctx)
    score = sum(c["weight"] for c in checks if c["passed"])
    rules = lesson.manifest["validation"]
    critical_ok = all(c["passed"] for c in checks if c["critical"])
    passed = score >= rules["minimum_score"] and (
        critical_ok or not rules["require_all_critical_checks"]
    )
    return {"passed": passed, "score": score, "checks": checks}
