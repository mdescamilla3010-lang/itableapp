"""Password hashing and session tokens (JWT) shared by both login paths:
real user accounts (app.api.v1.endpoints.auth) and the legacy per-tenant
access code (app.api.v1.endpoints.tenants) — both end up issuing the same
kind of token, checked by app.api.deps against every tenant-scoped endpoint.
"""

import datetime
import uuid

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7


class InvalidTokenError(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(*, tenant_id: uuid.UUID, role: str, user_id: uuid.UUID | None = None) -> str:
    now = datetime.datetime.now(datetime.UTC)
    payload = {
        "tenant_id": str(tenant_id),
        "role": role,
        "user_id": str(user_id) if user_id else None,
        "iat": now,
        "exp": now + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError from exc
