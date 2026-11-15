"""Azure Databricks backend: a shared SQL warehouse and Unity Catalog.

Isolation model for the pilot:

- Each execution gets a new schema with a random name. The worker drops it
  after grading. A sweep drops schemas that a stopped worker left.
- The learner SQL guard permits only relations from `source()` and `ref()`,
  so a model cannot name the schema of a different run.
- The service principal has rights in the lab catalog only.

One service principal runs all learner SQL. For a public launch, use one
principal for each learner. See docs/databricks.md.
"""

import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .base import Backend, Query, RunContext

_NAME = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
_HOST = re.compile(r"^[a-z0-9.-]+$")
_HTTP_PATH = re.compile(r"^/[A-Za-z0-9/_.?=-]+$")
CONNECT_TIMEOUT_SECONDS = 60


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Credential:
    """OAuth machine-to-machine (preferred) or a personal access token."""

    client_id: str = ""
    client_secret: str = ""
    token: str = ""

    @property
    def is_set(self) -> bool:
        return bool(self.token or (self.client_id and self.client_secret))

    def secrets(self) -> list[str]:
        return [v for v in (self.client_secret, self.token) if v]


@dataclass(frozen=True)
class DatabricksSettings:
    host: str
    http_path: str
    catalog: str
    runner: Credential
    # Optional read-only principal for the grader. Falls back to the runner.
    grader: Credential
    schema_prefix: str = "df_run_"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "DatabricksSettings":
        env = os.environ if env is None else env

        def credential(prefix: str) -> Credential:
            return Credential(
                client_id=env.get(f"{prefix}CLIENT_ID", ""),
                client_secret=env.get(f"{prefix}CLIENT_SECRET", ""),
                token=env.get(f"{prefix}TOKEN", ""),
            )

        host = env.get("DF_DBX_HOST", "").removeprefix("https://").rstrip("/").lower()
        settings = cls(
            host=host,
            http_path=env.get("DF_DBX_HTTP_PATH", ""),
            catalog=env.get("DF_DBX_CATALOG", ""),
            runner=credential("DF_DBX_"),
            grader=credential("DF_DBX_GRADER_"),
            schema_prefix=env.get("DF_DBX_SCHEMA_PREFIX", "df_run_"),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        # These values go into SQL and YAML, so the formats are strict.
        if not _HOST.match(self.host):
            raise ConfigError(
                "DF_DBX_HOST must be a host name, for example adb-123.4.azuredatabricks.net"
            )
        if not _HTTP_PATH.match(self.http_path):
            raise ConfigError("DF_DBX_HTTP_PATH must be the HTTP path of a SQL warehouse")
        if not _NAME.match(self.catalog):
            raise ConfigError("DF_DBX_CATALOG must be lowercase letters, digits and underscores")
        if not _NAME.match(self.schema_prefix) or len(self.schema_prefix) > 20:
            raise ConfigError("DF_DBX_SCHEMA_PREFIX must be a short lowercase name")
        if not self.runner.is_set:
            raise ConfigError(
                "Set DF_DBX_CLIENT_ID and DF_DBX_CLIENT_SECRET (preferred), or DF_DBX_TOKEN"
            )


Connect = Callable[[DatabricksSettings, Credential], "object"]


def _connect(settings: DatabricksSettings, credential: Credential):
    """Open a SQL warehouse connection. Imported late: the API does not need it."""
    from databricks import sql

    # Time limits, so that a warehouse that does not answer cannot stop the worker.
    limits = {
        "_socket_timeout": CONNECT_TIMEOUT_SECONDS,
        "_retry_stop_after_attempts_duration": CONNECT_TIMEOUT_SECONDS,
    }
    if credential.token:
        return sql.connect(
            server_hostname=settings.host,
            http_path=settings.http_path,
            access_token=credential.token,
            **limits,
        )

    from databricks.sdk.core import Config, oauth_service_principal

    def provider():
        return oauth_service_principal(
            Config(
                host=f"https://{settings.host}",
                client_id=credential.client_id,
                client_secret=credential.client_secret,
                http_timeout_seconds=CONNECT_TIMEOUT_SECONDS,
                retry_timeout_seconds=CONNECT_TIMEOUT_SECONDS,
            )
        )

    return sql.connect(
        server_hostname=settings.host,
        http_path=settings.http_path,
        credentials_provider=provider,
        **limits,
    )


class DatabricksBackend(Backend):
    name = "databricks"
    dialect = "databricks"
    seed_target = "lab"
    build_target = "lab"

    def __init__(self, settings: DatabricksSettings, connect: Connect = _connect):
        self.settings = settings
        self._connect = connect

    def new_context(self, execution_id: str, workspace: Path) -> RunContext:
        suffix = re.sub(r"[^a-f0-9]", "", execution_id.lower())
        if len(suffix) != 32:
            raise ValueError("execution id must be a UUID")
        return RunContext(execution_id, workspace, f"{self.settings.schema_prefix}{suffix}")

    def profile(self, ctx: RunContext) -> dict:
        output = {
            "type": "databricks",
            "catalog": self.settings.catalog,
            "schema": ctx.schema,
            "host": self.settings.host,
            "http_path": self.settings.http_path,
            "threads": 1,
        }
        # Secrets stay in the environment. They are not written to the workspace.
        if self.settings.runner.token:
            output["token"] = "{{ env_var('DF_DBX_TOKEN') }}"
        else:
            output["auth_type"] = "oauth"
            output["client_id"] = "{{ env_var('DF_DBX_CLIENT_ID') }}"
            output["client_secret"] = "{{ env_var('DF_DBX_CLIENT_SECRET') }}"
        return {"lab": output}

    def env(self, ctx: RunContext) -> dict[str, str]:
        runner = self.settings.runner
        if runner.token:
            return {"DF_DBX_TOKEN": runner.token}
        return {"DF_DBX_CLIENT_ID": runner.client_id, "DF_DBX_CLIENT_SECRET": runner.client_secret}

    def secrets(self) -> list[str]:
        # The workspace address is not a secret, but a learner does not need it.
        return [
            *self.settings.runner.secrets(),
            *self.settings.grader.secrets(),
            self.settings.host,
            self.settings.http_path,
        ]

    def _schema_sql(self, schema: str) -> str:
        if not _NAME.match(schema) or not schema.startswith(self.settings.schema_prefix):
            raise ValueError(f"not a run schema: {schema!r}")
        return f"`{self.settings.catalog}`.`{schema}`"

    def relation(self, ctx: RunContext, table: str) -> str:
        if not _NAME.match(table):
            raise ValueError(f"bad table name: {table!r}")
        return f"{self._schema_sql(ctx.schema)}.`{table}`"

    @contextmanager
    def _query(self, credential: Credential) -> Iterator[Query]:
        connection = self._connect(self.settings, credential)
        try:

            def query(sql: str) -> list[tuple]:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    if cursor.description is None:
                        return []
                    return [tuple(row) for row in cursor.fetchall()]

            yield query
        finally:
            connection.close()

    @contextmanager
    def grader_query(self, ctx: RunContext) -> Iterator[Query]:
        grader = self.settings.grader
        with self._query(grader if grader.is_set else self.settings.runner) as query:
            yield query

    def columns(self, query: Query, ctx: RunContext, table: str) -> list[tuple[str, str]]:
        if not _NAME.match(table):
            raise ValueError(f"bad table name: {table!r}")
        self._schema_sql(ctx.schema)  # validates the schema name
        rows = query(
            "select column_name, data_type "
            f"from `{self.settings.catalog}`.information_schema.columns "
            f"where table_schema = '{ctx.schema}' and table_name = '{table}' "
            "order by ordinal_position"
        )
        return [(r[0], str(r[1]).upper()) for r in rows]

    def cleanup(self, ctx: RunContext) -> None:
        with self._query(self.settings.runner) as query:
            query(f"drop schema if exists {self._schema_sql(ctx.schema)} cascade")

    def sweep(self, max_age_minutes: int) -> int:
        """Drop run schemas older than the limit (left by a stopped worker)."""
        with self._query(self.settings.runner) as query:
            rows = query(
                "select schema_name "
                f"from `{self.settings.catalog}`.information_schema.schemata "
                f"where startswith(schema_name, '{self.settings.schema_prefix}') "
                f"and created < current_timestamp() - interval {int(max_age_minutes)} minutes"
            )
            for (schema,) in rows:
                query(f"drop schema if exists {self._schema_sql(schema)} cascade")
            return len(rows)
