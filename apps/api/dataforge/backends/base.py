"""Execution backend interface.

A backend is the SQL engine that runs a lesson. The runner and the grader
use only this interface, so a lesson runs the same way on each engine.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

Query = Callable[[str], list[tuple]]


@dataclass(frozen=True)
class RunContext:
    """One execution: its workspace and the schema that holds its tables."""

    execution_id: str
    workspace: Path
    schema: str


class Backend(ABC):
    name: str
    # SQL dialect for the learner SQL guard.
    dialect: str
    # dbt targets. The seed step is trusted. The build step runs learner SQL.
    seed_target: str
    build_target: str

    @abstractmethod
    def new_context(self, execution_id: str, workspace: Path) -> RunContext: ...

    @abstractmethod
    def profile(self, ctx: RunContext) -> dict:
        """dbt outputs, by target name. Secrets must be `env_var()` references."""

    @abstractmethod
    def env(self, ctx: RunContext) -> dict[str, str]:
        """Environment variables that dbt needs for this backend."""

    def secrets(self) -> list[str]:
        """Values that must not show in learner logs."""
        return []

    @abstractmethod
    def relation(self, ctx: RunContext, table: str) -> str:
        """Full SQL name of a table that the run made."""

    @abstractmethod
    @contextmanager
    def grader_query(self, ctx: RunContext) -> Iterator[Query]:
        """Read-only query function for the grader."""

    @abstractmethod
    def columns(self, query: Query, ctx: RunContext, table: str) -> list[tuple[str, str]]:
        """Column names and uppercase type names, in table order."""

    def cleanup(self, ctx: RunContext) -> None:  # noqa: B027 - optional hook
        """Remove what the run made outside the workspace."""

    def sweep(self, max_age_minutes: int) -> int:
        """Remove what stopped workers left. Returns the number removed."""
        return 0
