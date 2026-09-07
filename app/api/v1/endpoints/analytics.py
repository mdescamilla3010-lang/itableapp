import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Tenant
from app.schemas.analytics import CajaAuditReport, FugasAuditReport, MenuEngineeringReport
from app.services.analytics_caja import CajaAnalyticsEngine
from app.services.analytics_fugas import FugasAnalyticsEngine
from app.services.analytics_menu import MenuEngineeringEngine

router = APIRouter()


def _ensure_tenant_exists(tenant_id: uuid.UUID, db: Session) -> None:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.get("/analytics/staff-audit/{tenant_id}", response_model=FugasAuditReport)
def get_staff_audit(
    tenant_id: uuid.UUID, branch_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> FugasAuditReport:
    _ensure_tenant_exists(tenant_id, db)
    engine = FugasAnalyticsEngine(db=db, tenant_id=tenant_id, branch_id=branch_id)
    return engine.analyze_waiter_anomalies()


@router.get("/analytics/cash-audit/{tenant_id}", response_model=CajaAuditReport)
def get_cash_audit(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> CajaAuditReport:
    _ensure_tenant_exists(tenant_id, db)
    engine = CajaAnalyticsEngine(db=db, tenant_id=tenant_id)
    return engine.analyze_cashier_discrepancies()


@router.get("/analytics/menu-engineering/{tenant_id}", response_model=MenuEngineeringReport)
def get_menu_engineering(
    tenant_id: uuid.UUID, branch_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> MenuEngineeringReport:
    _ensure_tenant_exists(tenant_id, db)
    engine = MenuEngineeringEngine(db=db, tenant_id=tenant_id, branch_id=branch_id)
    return engine.analyze_menu()
