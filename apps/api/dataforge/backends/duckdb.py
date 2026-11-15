"""DuckDB backend: one database file in the workspace. No cloud account."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb

from .base import Backend, Query, RunContext

DUCKDB_FILE = "lab.duckdb"


class DuckDBBackend(Backend):
    name = "duckdb"
    dialect = "duckdb"
    seed_target = "seed"
    build_target = "learner"

    def new_context(self, execution_id: str, workspace: Path) -> RunContext:
        return RunContext(execution_id, workspace, "main")

    def profile(self, ctx: RunContext) -> dict:
        base = {
            "type": "duckdb",
            "path": "{{ env_var('DF_DUCKDB_PATH') }}",
            "schema": ctx.schema,
            "threads": 1,
        }
        return {
            # Trusted step only: loads the seed file. Runs before learner SQL.
            "seed": dict(base),
            # Learner SQL runs here. It must not read or write files, or load
            # extensions. DuckDB does not let a session enable this access again.
            "learner": {
                **base,
                "settings": {
                    "enable_external_access": False,
                    "autoinstall_known_extensions": False,
                    "autoload_known_extensions": False,
                },
            },
        }

    def env(self, ctx: RunContext) -> dict[str, str]:
        return {"DF_DUCKDB_PATH": str(ctx.workspace / DUCKDB_FILE)}

    def relation(self, ctx: RunContext, table: str) -> str:
        return f'"{ctx.schema}"."{table}"'

    @contextmanager
    def grader_query(self, ctx: RunContext) -> Iterator[Query]:
        con = duckdb.connect(str(ctx.workspace / DUCKDB_FILE), read_only=True)
        try:
            yield lambda sql: con.execute(sql).fetchall()
        finally:
            con.close()

    def columns(self, query: Query, ctx: RunContext, table: str) -> list[tuple[str, str]]:
        rows = query(f"describe {self.relation(ctx, table)}")
        return [(r[0], str(r[1]).upper()) for r in rows]
