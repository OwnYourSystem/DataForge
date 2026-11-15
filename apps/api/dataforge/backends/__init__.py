"""Execution backends. `DF_EXECUTION_BACKEND` selects one."""

from .. import config
from .base import Backend, Query, RunContext

__all__ = ["Backend", "Query", "RunContext", "load", "dialect"]

NAMES = ("duckdb", "databricks")


def dialect(name: str | None = None) -> str:
    """SQL dialect of the configured backend. The API uses this for the guard."""
    name = name or config.execution_backend()
    if name not in NAMES:
        raise ValueError(f"unknown execution backend: {name!r}")
    return name


def load(name: str | None = None) -> Backend:
    name = dialect(name)
    if name == "databricks":
        from .databricks import DatabricksBackend, DatabricksSettings

        return DatabricksBackend(DatabricksSettings.from_env())
    from .duckdb import DuckDBBackend

    return DuckDBBackend()
