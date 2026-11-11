"""Token verification. A local key pair takes the place of the provider."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi.testclient import TestClient

from dataforge import auth
from dataforge.db import make_engine
from dataforge.main import create_app

ISSUER = "https://abcdefghijkl.supabase.co/auth/v1"
AUDIENCE = "authenticated"
KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())


def token(key=KEY, algorithm="ES256", **overrides):
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "0b0f4b0e-1111-4222-8333-444455556666",
        "exp": int(time.time()) + 600,
        "email": "learner@example.com",
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm=algorithm)


@pytest.fixture()
def client(lessons, monkeypatch):
    monkeypatch.setenv("DF_AUTH_MODE", "jwt")
    monkeypatch.setenv("DF_AUTH_ISSUER", ISSUER)
    monkeypatch.setenv("DF_AUTH_AUDIENCE", AUDIENCE)
    verifier = auth.JwtVerifier(
        auth.JwtSettings(ISSUER, AUDIENCE, f"{ISSUER}/.well-known/jwks.json"),
        signing_key=lambda _token: KEY.public_key(),
    )
    monkeypatch.setattr(auth, "_default_verifier", lambda: verifier)
    return TestClient(create_app(engine=make_engine("sqlite:///:memory:"), lessons=lessons))


def bearer(value):
    return {"Authorization": f"Bearer {value}"}


def test_valid_token_signs_in(client):
    response = client.get("/v1/me", headers=bearer(token()))
    assert response.status_code == 200
    assert response.json()["identity_subject"] == f"{ISSUER}|0b0f4b0e-1111-4222-8333-444455556666"


def test_same_subject_gets_the_same_user_and_project(client):
    first = client.post("/v1/projects", json={"lesson_id": "lab-001"}, headers=bearer(token()))
    second = client.post("/v1/projects", json={"lesson_id": "lab-001"}, headers=bearer(token()))
    other = client.post(
        "/v1/projects", json={"lesson_id": "lab-001"}, headers=bearer(token(sub="other-user"))
    )
    assert first.json()["id"] == second.json()["id"] != other.json()["id"]


def hs256_with_public_key():
    """Algorithm confusion: sign with HS256 and the public key as the secret."""
    public_pem = KEY.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    header = jwt.utils.base64url_encode(b'{"alg":"HS256","typ":"JWT"}')
    import hashlib
    import hmac
    import json

    payload = jwt.utils.base64url_encode(
        json.dumps(
            {"iss": ISSUER, "aud": AUDIENCE, "sub": "attacker", "exp": int(time.time()) + 600}
        ).encode()
    )
    signature = jwt.utils.base64url_encode(
        hmac.new(public_pem, header + b"." + payload, hashlib.sha256).digest()
    )
    return (header + b"." + payload + b"." + signature).decode()


REJECTED = {
    "no header": None,
    "not bearer": "Basic abc",
    "empty bearer": "Bearer ",
    "not a token": "Bearer not.a.token",
    "expired": lambda: f"Bearer {token(exp=int(time.time()) - 600)}",
    "no expiry": lambda: f"Bearer {token(exp=None)}",
    "wrong issuer": lambda: f"Bearer {token(iss='https://evil.example/auth/v1')}",
    "wrong audience": lambda: f"Bearer {token(aud='anon')}",
    "no subject": lambda: f"Bearer {token(sub=None)}",
    "empty subject": lambda: f"Bearer {token(sub='')}",
    "signed by a different key": lambda: f"Bearer {token(key=OTHER_KEY)}",
    "shared-secret algorithm": lambda: f"Bearer {token(key='guessable-secret', algorithm='HS256')}",
    "algorithm confusion": lambda: f"Bearer {hs256_with_public_key()}",
    "unsigned": lambda: (
        "Bearer "
        + jwt.encode(
            {"iss": ISSUER, "aud": AUDIENCE, "sub": "x", "exp": int(time.time()) + 600},
            key=None,
            algorithm="none",
        )
    ),
}


@pytest.mark.parametrize("case", REJECTED)
def test_bad_tokens_are_rejected(client, case):
    value = REJECTED[case]
    value = value() if callable(value) else value
    headers = {"Authorization": value} if value is not None else {}
    response = client.get("/v1/me", headers=headers)
    assert response.status_code == 401, case
    assert response.headers["www-authenticate"] == "Bearer"
    # One message for all token faults: the reason does not go to the client.
    assert response.json()["detail"] in (
        "Sign in to continue.",
        "Your session is not valid. Sign in again.",
    )


def test_dev_header_does_not_work_in_jwt_mode(client):
    assert client.get("/v1/me", headers={"X-Dev-User": "alice"}).status_code == 401


def test_rsa_tokens_are_accepted(lessons, monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = auth.JwtVerifier(
        auth.JwtSettings(ISSUER, AUDIENCE, "https://x/jwks"),
        signing_key=lambda _t: key.public_key(),
    )
    assert verifier.subject(token(key=key, algorithm="RS256")).endswith(
        "|0b0f4b0e-1111-4222-8333-444455556666"
    )


@pytest.mark.parametrize(
    "env",
    [
        {"DF_AUTH_ISSUER": "", "DF_AUTH_AUDIENCE": "authenticated"},
        {"DF_AUTH_ISSUER": "http://insecure.example", "DF_AUTH_AUDIENCE": "authenticated"},
        {"DF_AUTH_ISSUER": ISSUER, "DF_AUTH_AUDIENCE": ""},
        {"DF_AUTH_ISSUER": ISSUER, "DF_AUTH_AUDIENCE": "a", "DF_AUTH_JWKS_URL": "http://x/jwks"},
    ],
)
def test_the_api_does_not_start_with_bad_jwt_settings(lessons, monkeypatch, env):
    auth._default_verifier.cache_clear()
    monkeypatch.setenv("DF_AUTH_MODE", "jwt")
    for name in ("DF_AUTH_ISSUER", "DF_AUTH_AUDIENCE", "DF_AUTH_JWKS_URL"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(auth.AuthConfigError):
        create_app(engine=make_engine("sqlite:///:memory:"), lessons=lessons)
    auth._default_verifier.cache_clear()


def test_the_api_does_not_start_with_an_unknown_mode(lessons, monkeypatch):
    monkeypatch.setenv("DF_AUTH_MODE", "off")
    with pytest.raises(auth.AuthConfigError):
        create_app(engine=make_engine("sqlite:///:memory:"), lessons=lessons)


def test_default_jwks_url_comes_from_the_issuer(monkeypatch):
    monkeypatch.setenv("DF_AUTH_ISSUER", ISSUER + "/")
    monkeypatch.setenv("DF_AUTH_AUDIENCE", AUDIENCE)
    monkeypatch.delenv("DF_AUTH_JWKS_URL", raising=False)
    settings = auth.JwtSettings.from_env()
    assert settings.issuer == ISSUER
    assert settings.jwks_url == f"{ISSUER}/.well-known/jwks.json"
