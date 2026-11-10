"""Settings from environment variables."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./dataforge.db")


def curriculum_dir() -> Path:
    return Path(os.environ.get("DF_CURRICULUM_DIR", REPO_ROOT / "curriculum"))


def auth_mode() -> str:
    """`dev` trusts the X-Dev-User header. Do not use `dev` on a public host."""
    return os.environ.get("DF_AUTH_MODE", "dev")


def execution_timeout_seconds() -> int:
    return int(os.environ.get("DF_EXECUTION_TIMEOUT_SECONDS", "120"))


def cors_origins() -> list[str]:
    return os.environ.get("DF_CORS_ORIGINS", "http://localhost:3000").split(",")
