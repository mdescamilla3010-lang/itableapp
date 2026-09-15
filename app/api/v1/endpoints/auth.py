from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthSession, get_current_session
from app.core.security import create_access_token, verify_password
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos")

    token = create_access_token(tenant_id=user.tenant_id, role=user.role, user_id=user.id)
    return TokenResponse(access_token=token, tenant_id=user.tenant_id, role=user.role)


@router.get("/auth/me", response_model=MeResponse)
def get_me(session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)) -> User:
    if session.user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This session has no user account")

    user = db.execute(select(User).where(User.id == session.user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
