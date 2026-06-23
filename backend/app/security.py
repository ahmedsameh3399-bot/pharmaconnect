"""Password hashing and JWT helpers.

Why bcrypt (not plain SHA-256)? Bcrypt is intentionally slow and salted, which
defeats rainbow-table attacks and brute force at scale. The cost factor is the
log2 of the number of internal rounds; 12 is the modern default.

Why JWT? Stateless auth - the server can verify a token without a DB lookup,
which keeps the API fast and horizontally scalable. We pair a short-lived
access token (30 min) with a longer refresh token (7 days) to limit damage if
an access token leaks.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        token_type="refresh",
    )


def decode_token(token: str, expected_type: str) -> int:
    """Return the user_id encoded in the token. Raises JWTError on any problem."""
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise JWTError(f"Wrong token type: expected {expected_type}")
    sub = payload.get("sub")
    if sub is None:
        raise JWTError("Token missing sub claim")
    return int(sub)


def generate_password_reset_token() -> tuple[str, str]:
    """Return (plaintext_token, hashed_token).

    The plaintext is emailed to the user; only the hash is stored in DB so a
    DB leak doesn't give an attacker working reset links.
    """
    plaintext = secrets.token_urlsafe(32)
    return plaintext, pwd_context.hash(plaintext)
