import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Tenant
from app.schemas.cash_shift import CashShiftSyncResultResponse, ParrotCashShiftSyncPayload
from app.schemas.order import ParrotSyncPayload, SyncResultResponse
from app.services.ingestion import ParrotIngestionService

router = APIRouter()


def _get_tenant_or_404(tenant_id: uuid.UUID, db: Session) -> Tenant:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.post("/sync/{tenant_id}", response_model=SyncResultResponse, status_code=status.HTTP_201_CREATED)
def sync_orders(tenant_id: uuid.UUID, payload: ParrotSyncPayload, db: Session = Depends(get_db)) -> SyncResultResponse:
    _get_tenant_or_404(tenant_id, db)

    service = ParrotIngestionService(db=db, tenant_id=tenant_id)
    return service.process_orders_payload(payload)


@router.post(
    "/sync/{tenant_id}/cash-shifts",
    response_model=CashShiftSyncResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def sync_cash_shifts(
    tenant_id: uuid.UUID, payload: ParrotCashShiftSyncPayload, db: Session = Depends(get_db)
) -> CashShiftSyncResultResponse:
    _get_tenant_or_404(tenant_id, db)

    service = ParrotIngestionService(db=db, tenant_id=tenant_id)
    return service.process_cash_shifts_payload(payload)
