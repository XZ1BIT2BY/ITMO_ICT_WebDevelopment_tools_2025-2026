import os
import hmac
import hashlib
import json
import base64
import time
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24  # 24 часа


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * padding)


def create_access_token(user_id: int, username: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS,
        "iat": int(time.time()),
    }

    header_enc = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_enc = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())

    signing_input = f"{header_enc}.{payload_enc}"
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        header_enc, payload_enc, signature_enc = token.split(".")
    except ValueError:
        return None

    signing_input = f"{header_enc}.{payload_enc}"
    expected_sig = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(expected_sig, _b64url_decode(signature_enc)):
        return None

    payload = json.loads(_b64url_decode(payload_enc))

    if payload.get("exp", 0) < int(time.time()):
        return None

    return payload