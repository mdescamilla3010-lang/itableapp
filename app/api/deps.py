import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import InvalidTokenError, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthSession:
    tenant_id: uuid.UUID
    role: str
    user_id: uuid.UUID | None


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthSession:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")
    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    return AuthSession(
        tenant_id=uuid.UUID(payload["tenant_id"]),
        role=payload["role"],
        user_id=uuid.UUID(payload["user_id"]) if payload.get("user_id") else None,
    )


def require_tenant_match(
    tenant_id: uuid.UUID, session: AuthSession = Depends(get_current_session)
) -> AuthSession:
    if session.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Token does not grant access to this tenant"
        )
    return session
