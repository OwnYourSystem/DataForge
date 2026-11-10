"""Independent grading.

The grader does not trust the dbt exit code alone. It opens the result
database read-only and compares the table with values it calculates itself.
"""

import csv
import json
from pathlib import Path

import duckdb

from .curriculum import Lesson
from .runner import DUCKDB_FILE


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


def grade_lab_001(lesson: Lesson, workspace: Path) -> list[dict]:
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
    counts = (0, 0, 0)
    try:
        con = duckdb.connect(str(workspace / DUCKDB_FILE), read_only=True)
        try:
            columns = [(r[0], r[1]) for r in con.execute("describe main.stg_customers").fetchall()]
            counts = con.execute(
                "select count(*), count(distinct customer_key), "
                "count(*) filter (where customer_key is null) from main.stg_customers"
            ).fetchone()
            rows = sorted(
                con.execute(
                    "select customer_key, customer_name, email, country from main.stg_customers"
                ).fetchall(),
                key=repr,
            )
        finally:
            con.close()
    except duckdb.Error:
        pass  # The table or a column is missing. The checks below fail.

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


def grade(lesson: Lesson, workspace: Path) -> dict:
    checks = GRADERS[lesson.id](lesson, workspace)
    score = sum(c["weight"] for c in checks if c["passed"])
    rules = lesson.manifest["validation"]
    critical_ok = all(c["passed"] for c in checks if c["critical"])
    passed = score >= rules["minimum_score"] and (
        critical_ok or not rules["require_all_critical_checks"]
    )
    return {"passed": passed, "score": score, "checks": checks}
