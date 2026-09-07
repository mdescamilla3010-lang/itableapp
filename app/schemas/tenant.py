import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenantBase(BaseModel):
    name: str
    slug: str
    subscription_plan: str = "pro"
    is_active: bool = True


class TenantCreate(TenantBase):
    parrot_api_key: str | None = None


class TenantRead(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    code_required: bool = False


class TenantCreated(TenantRead):
    """Returned only from the create-tenant call: carries the plaintext
    access code, which is never retrievable again afterwards."""

    access_code: str


class AccessCodeVerifyRequest(BaseModel):
    code: str


class AccessCodeVerifyResponse(BaseModel):
    valid: bool


class AccessCodeRotateResponse(BaseModel):
    access_code: str


class BranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    external_id: str
    name: str


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    external_id: str
    name: str
    role: str
