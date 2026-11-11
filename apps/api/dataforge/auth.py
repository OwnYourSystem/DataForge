"""Identity.

Two modes, selected with `DF_AUTH_MODE`:

- `jwt`: the client sends `Authorization: Bearer <token>`. The API verifies
  the signature with the provider's public keys (JWKS), and the issuer,
  audience, and expiry. This works with Supabase Auth and with any OpenID
  Connect provider that signs tokens with an asymmetric key.
- `dev`: trusts the X-Dev-User header. For local work and CI only.

The remaining code uses only `identity_subject`, so the provider can change.
"""

import logging
import re
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient

from . import config

log = logging.getLogger("dataforge.auth")

_DEV_SUBJECT = re.compile(r"^[A-Za-z0-9_.@-]{1,64}$")
# Asymmetric algorithms only. A shared-secret algorithm (HS256) would let a
# person who knows a public value forge a token.
ALGORITHMS = ["ES256", "RS256", "EdDSA"]
_UNAUTHORIZED = {"WWW-Authenticate": "Bearer"}


class AuthConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class JwtSettings:
    issuer: str
    audience: str
    jwks_url: str

    @classmethod
    def from_env(cls) -> "JwtSettings":
        issuer = config.auth_issuer().rstrip("/")
        audience = config.auth_audience()
        jwks_url = config.auth_jwks_url() or f"{issuer}/.well-known/jwks.json"
        if not issuer.startswith("https://") or not audience:
            raise AuthConfigError(
                "DF_AUTH_MODE=jwt needs DF_AUTH_ISSUER (https URL) and DF_AUTH_AUDIENCE"
            )
        if not jwks_url.startswith("https://"):
            raise AuthConfigError("DF_AUTH_JWKS_URL must be an https URL")
        return cls(issuer, audience, jwks_url)


class JwtVerifier:
    def __init__(self, settings: JwtSettings, signing_key=None):
        self.settings = settings
        # `signing_key(token)` returns the public key for a token. Tests pass one.
        if signing_key is None:
            client = PyJWKClient(settings.jwks_url, cache_keys=True, lifespan=3600, timeout=10)
            signing_key = lambda token: client.get_signing_key_from_jwt(token).key  # noqa: E731
        self._signing_key = signing_key

    def subject(self, token: str) -> str:
        """Return the identity subject, or raise jwt.PyJWTError."""
        claims = jwt.decode(
            token,
            self._signing_key(token),
            algorithms=ALGORITHMS,
            issuer=self.settings.issuer,
            audience=self.settings.audience,
            options={"require": ["exp", "iss", "aud", "sub"]},
            leeway=30,
        )
        subject = claims["sub"]
        if not isinstance(subject, str) or not 1 <= len(subject) <= 128:
            raise jwt.InvalidTokenError("bad subject")
        # The issuer is part of the identity: two providers can use the same `sub`.
        return f"{self.settings.issuer}|{subject}"


@lru_cache(maxsize=1)
def _default_verifier() -> JwtVerifier:
    return JwtVerifier(JwtSettings.from_env())


def check_startup_config() -> None:
    """Fail at startup, not at the first request, when the settings are wrong."""
    mode = config.auth_mode()
    if mode == "jwt":
        _default_verifier()
    elif mode == "dev":
        log.warning("DF_AUTH_MODE=dev: the API trusts the X-Dev-User header. Local use only.")
    else:
        raise AuthConfigError(f"unknown DF_AUTH_MODE: {mode!r}")


def identity_subject(
    authorization: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None),
) -> str:
    mode = config.auth_mode()
    if mode == "dev":
        if not x_dev_user or not _DEV_SUBJECT.match(x_dev_user):
            raise HTTPException(401, "Send a valid X-Dev-User header.")
        return f"dev:{x_dev_user}"
    if mode != "jwt":
        raise HTTPException(500, "The identity provider is not configured.")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Sign in to continue.", headers=_UNAUTHORIZED)
    try:
        return _default_verifier().subject(token.strip())
    except jwt.PyJWTError as exc:
        # The reason goes to the log only. The client gets one message.
        log.info("token rejected: %s", type(exc).__name__)
        raise HTTPException(
            401, "Your session is not valid. Sign in again.", headers=_UNAUTHORIZED
        ) from exc
