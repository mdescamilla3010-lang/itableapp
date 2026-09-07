"""Lightweight per-tenant access code: a shared passcode (like a meeting PIN),
not a user account system. Gates who can view a tenant's dashboards without
requiring full authentication infrastructure.
"""

import hashlib
import hmac
import secrets

from app.core.config import settings

_CODE_ALPHABET = "0123456789"
_CODE_LENGTH = 6


def generate_access_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def hash_access_code(code: str) -> str:
    digest = hashlib.sha256(f"{settings.SECRET_KEY}:{code}".encode()).hexdigest()
    return digest


def verify_access_code(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_access_code(code), code_hash)
