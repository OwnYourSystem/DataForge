"""Azure Databricks backend: a shared SQL warehouse and Unity Catalog.

Two service principals, with different rights (see docs/adr/004-run-isolation.md):

- The platform principal is trusted. It makes the schema of a run, loads the
  lesson data, gives the learner principal rights on that schema, reads the
  result for the grader, and drops the schema.
- The learner principal is not trusted. It runs the learner model. It has
  rights on the schema of the current run only. It cannot make a schema.

One worker has one learner principal. To run more than one execution at the
same time, give each worker its own learner principal.
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
# An application id (UUID) or a user name. It goes into a GRANT statement.
_PRINCIPAL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$")
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
    # Trusted: makes and drops run schemas, loads lesson data, reads results.
    platform: Credential
    # Not trusted: runs learner SQL with rights on one run schema only.
    learner: Credential
    # The name of the learner principal in a GRANT statement. For OAuth this is
    # the application id, which is also the client id.
    learner_principal: str
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
        learner = credential("DF_DBX_LEARNER_")
        settings = cls(
            host=host,
            http_path=env.get("DF_DBX_HTTP_PATH", ""),
            catalog=env.get("DF_DBX_CATALOG", ""),
            platform=credential("DF_DBX_PLATFORM_"),
            learner=learner,
            learner_principal=env.get("DF_DBX_LEARNER_PRINCIPAL", "") or learner.client_id,
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
        for name, credential in (("PLATFORM", self.platform), ("LEARNER", self.learner)):
            if not credential.is_set:
                raise ConfigError(
                    f"Set DF_DBX_{name}_CLIENT_ID and DF_DBX_{name}_CLIENT_SECRET (preferred), "
                    f"or DF_DBX_{name}_TOKEN"
                )
        if self.platform == self.learner:
            raise ConfigError("The platform principal and the learner principal must be different")
        if not _PRINCIPAL.match(self.learner_principal):
            raise ConfigError(
                "DF_DBX_LEARNER_PRINCIPAL must be the application id or the name of the "
                "learner principal"
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
    seed_target = "seed"
    build_target = "learner"

    def __init__(self, settings: DatabricksSettings, connect: Connect = _connect):
        self.settings = settings
        self._connect = connect

    def new_context(self, execution_id: str, workspace: Path) -> RunContext:
        suffix = re.sub(r"[^a-f0-9]", "", execution_id.lower())
        if len(suffix) != 32:
            raise ValueError("execution id must be a UUID")
        return RunContext(execution_id, workspace, f"{self.settings.schema_prefix}{suffix}")

    def _output(self, ctx: RunContext, credential: Credential, prefix: str) -> dict:
        output = {
            "type": "databricks",
            "catalog": self.settings.catalog,
            "schema": ctx.schema,
            "host": self.settings.host,
            "http_path": self.settings.http_path,
            "threads": 1,
        }
        # Secrets stay in the environment. They are not written to the workspace.
        if credential.token:
            output["token"] = f"{{{{ env_var('{prefix}TOKEN') }}}}"
        else:
            output["auth_type"] = "oauth"
            output["client_id"] = f"{{{{ env_var('{prefix}CLIENT_ID') }}}}"
            output["client_secret"] = f"{{{{ env_var('{prefix}CLIENT_SECRET') }}}}"
        return output

    def profile(self, ctx: RunContext) -> dict:
        return {
            # Trusted step: the platform principal loads the lesson data.
            "seed": self._output(ctx, self.settings.platform, "DF_DBX_PLATFORM_"),
            # Learner SQL runs as the learner principal.
            "learner": self._output(ctx, self.settings.learner, "DF_DBX_LEARNER_"),
        }

    def env(self, ctx: RunContext, target: str) -> dict[str, str]:
        """Only the credential of this step. The learner step does not get the
        platform secret."""
        if target == "seed":
            credential, prefix = self.settings.platform, "DF_DBX_PLATFORM_"
        elif target == "learner":
            credential, prefix = self.settings.learner, "DF_DBX_LEARNER_"
        else:
            raise ValueError(f"unknown target: {target!r}")
        if credential.token:
            return {f"{prefix}TOKEN": credential.token}
        return {
            f"{prefix}CLIENT_ID": credential.client_id,
            f"{prefix}CLIENT_SECRET": credential.client_secret,
        }

    def secrets(self) -> list[str]:
        # The workspace address is not a secret, but a learner does not need it.
        return [
            *self.settings.platform.secrets(),
            *self.settings.learner.secrets(),
            self.settings.host,
            self.settings.http_path,
        ]

    def prepare(self, ctx: RunContext) -> None:
        """Make the schema of the run and give the learner principal rights on it.

        The learner principal gets no right to change the lesson data: tables
        that the platform principal loads stay read-only for it.
        """
        schema = self._schema_sql(ctx.schema)
        with self._query(self.settings.platform) as query:
            query(f"create schema if not exists {schema} comment 'DataForge run'")
            query(
                f"grant use schema, create table, select on schema {schema} "
                f"to `{self.settings.learner_principal}`"
            )

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
        with self._query(self.settings.platform) as query:
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
        with self._query(self.settings.platform) as query:
            query(f"drop schema if exists {self._schema_sql(ctx.schema)} cascade")

    def sweep(self, max_age_minutes: int) -> int:
        """Drop run schemas older than the limit (left by a stopped worker)."""
        with self._query(self.settings.platform) as query:
            rows = query(
                "select schema_name "
                f"from `{self.settings.catalog}`.information_schema.schemata "
                f"where startswith(schema_name, '{self.settings.schema_prefix}') "
                f"and created < current_timestamp() - interval {int(max_age_minutes)} minutes"
            )
            for (schema,) in rows:
                query(f"drop schema if exists {self._schema_sql(schema)} cascade")
            return len(rows)
