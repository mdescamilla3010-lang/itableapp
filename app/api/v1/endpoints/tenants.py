import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.access_code import generate_access_code, hash_access_code, verify_access_code
from app.db.database import get_db
from app.db.models import Branch, Tenant
from app.schemas.tenant import (
    AccessCodeRotateResponse,
    AccessCodeVerifyRequest,
    AccessCodeVerifyResponse,
    BranchRead,
    TenantCreate,
    TenantCreated,
    TenantRead,
)

router = APIRouter()


@router.get("/tenants", response_model=list[TenantRead])
def list_tenants(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[Tenant]:
    stmt = select(Tenant).order_by(Tenant.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@router.post("/tenants", response_model=TenantCreated, status_code=status.HTTP_201_CREATED)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)) -> TenantCreated:
    access_code = generate_access_code()
    tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        parrot_api_key=payload.parrot_api_key,
        subscription_plan=payload.subscription_plan,
        is_active=payload.is_active,
        access_code_hash=hash_access_code(access_code),
    )
    db.add(tenant)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{payload.slug}' already exists",
        ) from exc

    db.refresh(tenant)
    return TenantCreated(**TenantRead.model_validate(tenant).model_dump(), access_code=access_code)


@router.get("/tenants/{tenant_id}", response_model=TenantRead)
def get_tenant(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> Tenant:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.post("/tenants/{tenant_id}/verify-access", response_model=AccessCodeVerifyResponse)
def verify_tenant_access(
    tenant_id: uuid.UUID, payload: AccessCodeVerifyRequest, db: Session = Depends(get_db)
) -> AccessCodeVerifyResponse:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    if tenant.access_code_hash is None:
        # Tenants created before this feature existed have no code set yet.
        return AccessCodeVerifyResponse(valid=True)

    return AccessCodeVerifyResponse(valid=verify_access_code(payload.code, tenant.access_code_hash))


@router.post("/tenants/{tenant_id}/rotate-access-code", response_model=AccessCodeRotateResponse)
def rotate_tenant_access_code(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> AccessCodeRotateResponse:
    """Generates a new access code for a tenant, replacing any existing one.

    Use this to retroactively secure a tenant created before access codes
    existed, or to revoke a code that may have been shared too widely.
    """
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    access_code = generate_access_code()
    tenant.access_code_hash = hash_access_code(access_code)
    db.commit()

    return AccessCodeRotateResponse(access_code=access_code)


@router.get("/tenants/{tenant_id}/branches", response_model=list[BranchRead])
def list_tenant_branches(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Branch]:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    stmt = select(Branch).where(Branch.tenant_id == tenant_id).order_by(Branch.name)
    return list(db.execute(stmt).scalars().all())
