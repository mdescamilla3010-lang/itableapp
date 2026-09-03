import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Tenant
from app.schemas.order import ParrotSyncPayload, SyncResultResponse
from app.services.ingestion import ParrotIngestionService

router = APIRouter()


@router.post("/sync/{tenant_id}", response_model=SyncResultResponse, status_code=status.HTTP_201_CREATED)
def sync_orders(tenant_id: uuid.UUID, payload: ParrotSyncPayload, db: Session = Depends(get_db)) -> SyncResultResponse:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    service = ParrotIngestionService(db=db, tenant_id=tenant_id)
    return service.process_orders_payload(payload)
