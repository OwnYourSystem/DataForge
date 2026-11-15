"""Checks on learner SQL before it goes to dbt.

Two layers:

1. Jinja. dbt renders Jinja in model files. Jinja can read environment
   variables and run macros, so the learner gets only `source()` and `ref()`.
2. SQL. The model must be one query. It can read only relations that come
   from `source()` or `ref()`, and its own CTEs. This stops a learner who
   reads the tables of a different learner on a shared SQL warehouse.

The engine and its grants are the primary control. This guard is a second one.
"""

import logging
import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

# sqlglot logs a warning when it reads a statement as a raw command. The guard
# rejects those statements, so the warning is noise.
logging.getLogger("sqlglot").setLevel(logging.ERROR)

MAX_FILE_BYTES = 20_000

_ALLOWED_EXPRESSION = re.compile(
    r"""^\s*(
        source\(\s*(['"])[A-Za-z0-9_]+\2\s*,\s*(['"])[A-Za-z0-9_]+\3\s*\)
        |
        ref\(\s*(['"])[A-Za-z0-9_]+\4\s*\)
    )\s*$""",
    re.VERBOSE,
)
_EXPRESSION = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
_PLACEHOLDER = "df_relation_"

# Functions that reach outside the query: files, secrets, network, other SQL.
_DENIED_FUNCTIONS = {
    "secret", "reflect", "try_reflect", "java_method", "identifier", "query", "query_table",
    "getenv", "getvariable", "current_setting", "glob", "vector_search", "remote_query",
    "sql", "table", "stream", "cloud_files_state", "event_log", "list_secrets",
}  # fmt: skip
_DENIED_PREFIXES = ("read_", "ai_", "http_", "parquet_", "sniff_", "duckdb_", "pragma_", "pg_")


class GuardError(ValueError):
    pass


def _check_jinja(content: str) -> None:
    if "{%" in content or "%}" in content:
        raise GuardError("Jinja blocks ({% ... %}) are not permitted.")
    if "{#" in content or "#}" in content:
        raise GuardError("Jinja comments ({# ... #}) are not permitted. Use SQL comments.")
    for match in _EXPRESSION.finditer(content):
        if not _ALLOWED_EXPRESSION.match(match.group(1)):
            raise GuardError(
                "Only {{ source('name', 'table') }} and {{ ref('model') }} are permitted. "
                f"Found: {{{{{match.group(1)}}}}}"
            )
    remainder = _EXPRESSION.sub("", content)
    if "{{" in remainder or "}}" in remainder:
        raise GuardError("A Jinja expression is not closed correctly.")


def _function_name(node: exp.Func) -> str:
    if isinstance(node, exp.Anonymous):
        return str(node.this).lower()
    return node.sql_name().lower()


def _check_sql(content: str, dialect: str) -> None:
    if _PLACEHOLDER in content.lower():
        raise GuardError(f"The name `{_PLACEHOLDER}` is reserved.")
    counter = iter(range(1_000_000))
    sql = _EXPRESSION.sub(lambda _: f"{_PLACEHOLDER}{next(counter)}", content)
    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except (SqlglotError, RecursionError) as exc:
        first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else "syntax error"
        raise GuardError(f"The SQL has a syntax error: {first_line}") from exc
    if len(statements) != 1:
        raise GuardError("The model must contain one SQL query.")
    tree = statements[0]
    if not isinstance(tree, exp.Query):
        raise GuardError("The model must be a SELECT query.")

    for node in tree.walk():
        if isinstance(node, exp.Command | exp.DDL | exp.DML | exp.Set | exp.Pragma):
            raise GuardError("The model must be a SELECT query.")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        if not isinstance(table.this, exp.Identifier):
            raise GuardError("Table functions are not permitted. Read data with source() or ref().")
        name = table.name.lower()
        qualified = bool(table.args.get("db") or table.args.get("catalog"))
        if qualified or not (name.startswith(_PLACEHOLDER) or name in cte_names):
            raise GuardError(
                f"The model cannot read `{table.sql(dialect=dialect)}` directly. "
                "Read data with source() or ref()."
            )

    for node in tree.find_all(exp.Func):
        name = _function_name(node)
        if name in _DENIED_FUNCTIONS or name.startswith(_DENIED_PREFIXES):
            raise GuardError(f"The function `{name}` is not permitted.")


def check_learner_sql(content: str, dialect: str = "duckdb") -> None:
    """Raise GuardError if the file is not an approved dbt model."""
    if len(content.encode()) > MAX_FILE_BYTES:
        raise GuardError(f"The file is larger than {MAX_FILE_BYTES} bytes.")
    if "\x00" in content:
        raise GuardError("The file contains a NUL character.")
    _check_jinja(content)
    _check_sql(content, dialect)
