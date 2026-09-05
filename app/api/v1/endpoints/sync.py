import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Tenant
from app.schemas.cash_shift import (
    CashShiftsFileImportResponse,
    CashShiftSyncResultResponse,
    DemoDataSeedResponse,
    OrdersFileImportResponse,
    ParrotCashShiftSyncPayload,
)
from app.schemas.order import ParrotSyncPayload, SyncResultResponse
from app.services.demo_seed import generate_demo_cash_shifts_payload, generate_demo_orders_payload
from app.services.file_import import FileImportError, parse_cash_shifts_file, parse_orders_file
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


@router.post(
    "/sync/{tenant_id}/demo-data",
    response_model=DemoDataSeedResponse,
    status_code=status.HTTP_201_CREATED,
)
def seed_demo_data(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> DemoDataSeedResponse:
    """Populates the tenant with realistic sample orders and cash shifts for testing.

    Safe to call more than once: sample records use fixed external ids, so
    repeat calls are skipped as duplicates instead of piling up more data.
    """
    _get_tenant_or_404(tenant_id, db)

    service = ParrotIngestionService(db=db, tenant_id=tenant_id)
    orders_result = service.process_orders_payload(generate_demo_orders_payload())
    shifts_result = service.process_cash_shifts_payload(generate_demo_cash_shifts_payload())

    return DemoDataSeedResponse(orders=orders_result, cash_shifts=shifts_result)


@router.post(
    "/sync/{tenant_id}/upload/orders",
    response_model=OrdersFileImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_orders_file(
    tenant_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> OrdersFileImportResponse:
    """Ingests orders from a CSV/Excel export of any POS system.

    Required columns: external_order_id, external_product_id, product_name,
    order_date. Optional columns fill in staff, branch, discount, payment
    method, and total_amount (computed from items when omitted).
    """
    _get_tenant_or_404(tenant_id, db)

    try:
        payload, rows_skipped = parse_orders_file(await file.read(), file.filename or "")
    except FileImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    service = ParrotIngestionService(db=db, tenant_id=tenant_id)
    result = service.process_orders_payload(payload)
    return OrdersFileImportResponse(**result.model_dump(), rows_skipped_invalid=rows_skipped)


@router.post(
    "/sync/{tenant_id}/upload/cash-shifts",
    response_model=CashShiftsFileImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_cash_shifts_file(
    tenant_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db)
) -> CashShiftsFileImportResponse:
    """Ingests cash shifts from a CSV/Excel export of any POS system.

    Required columns: external_shift_id, expected_cash, actual_cash,
    shift_start. Optional columns: staff_external_id, staff_name, shift_end.
    """
    _get_tenant_or_404(tenant_id, db)

    try:
        payload, rows_skipped = parse_cash_shifts_file(await file.read(), file.filename or "")
    except FileImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    service = ParrotIngestionService(db=db, tenant_id=tenant_id)
    result = service.process_cash_shifts_payload(payload)
    return CashShiftsFileImportResponse(**result.model_dump(), rows_skipped_invalid=rows_skipped)
