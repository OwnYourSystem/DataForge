"""Settings from environment variables."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "sqlite:///./dataforge.db")
    # Hosts such as Render give `postgres://` or `postgresql://`. SQLAlchemy
    # needs the driver name, and this project uses psycopg 3.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def curriculum_dir() -> Path:
    return Path(os.environ.get("DF_CURRICULUM_DIR", REPO_ROOT / "curriculum"))


def auth_mode() -> str:
    """`jwt` verifies bearer tokens. `dev` trusts the X-Dev-User header: do not
    use `dev` on a public host."""
    return os.environ.get("DF_AUTH_MODE", "dev")


def auth_issuer() -> str:
    """Token issuer. For Supabase: https://<project-ref>.supabase.co/auth/v1"""
    return os.environ.get("DF_AUTH_ISSUER", "")


def auth_audience() -> str:
    """Expected audience. For Supabase: authenticated"""
    return os.environ.get("DF_AUTH_AUDIENCE", "")


def auth_jwks_url() -> str:
    """Public keys of the issuer. Default: <issuer>/.well-known/jwks.json"""
    return os.environ.get("DF_AUTH_JWKS_URL", "")


def execution_timeout_seconds() -> int:
    return int(os.environ.get("DF_EXECUTION_TIMEOUT_SECONDS", "120"))


def cors_origins() -> list[str]:
    """Origins that can call the API from a browser. Empty by default: the web
    app calls the API through its own server, so no browser origin needs access."""
    return [o for o in os.environ.get("DF_CORS_ORIGINS", "").split(",") if o]


def execution_backend() -> str:
    """`duckdb` (default, no cloud account) or `databricks`."""
    return os.environ.get("DF_EXECUTION_BACKEND", "duckdb")


def sweep_interval_seconds() -> int:
    return int(os.environ.get("DF_SWEEP_INTERVAL_SECONDS", "600"))


def backend_call_timeout_seconds() -> int:
    """Time limit for one grading or cleanup call to the backend."""
    return int(os.environ.get("DF_BACKEND_CALL_TIMEOUT_SECONDS", "180"))
