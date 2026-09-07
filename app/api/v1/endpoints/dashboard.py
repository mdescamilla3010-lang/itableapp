import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Order, Tenant
from app.schemas.analytics import DashboardSummary, MenuCategory, TopDogProduct, TopWaiterRisk
from app.services.analytics_fugas import FugasAnalyticsEngine
from app.services.analytics_menu import MenuEngineeringEngine

router = APIRouter()


@router.get("/dashboard/summary/{tenant_id}", response_model=DashboardSummary)
def get_dashboard_summary(
    tenant_id: uuid.UUID, branch_id: uuid.UUID | None = None, db: Session = Depends(get_db)
) -> DashboardSummary:
    tenant = db.execute(select(Tenant).where(Tenant.id == tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    sales_stmt = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
        Order.tenant_id == tenant_id, Order.status != "CANCELLED"
    )
    if branch_id is not None:
        sales_stmt = sales_stmt.where(Order.branch_id == branch_id)
    total_sales = db.execute(sales_stmt).scalar_one()

    fugas_report = FugasAnalyticsEngine(db=db, tenant_id=tenant_id, branch_id=branch_id).analyze_waiter_anomalies()
    menu_report = MenuEngineeringEngine(db=db, tenant_id=tenant_id, branch_id=branch_id).analyze_menu()

    top_risk_waiters = [
        TopWaiterRisk(
            staff_name=w.staff_name,
            zscore=w.zscore,
            total_cancelled_amount=w.total_cancelled_amount,
            risk_level=w.risk_level,
        )
        for w in fugas_report.waiters[:3]
    ]

    dog_products = [item for item in menu_report.items if item.menu_category == MenuCategory.PERRO]
    top_dog_products = [
        TopDogProduct(
            product_name=item.product_name,
            quantity_sold=item.quantity_sold,
            unit_margin=item.unit_margin,
        )
        for item in dog_products[:3]
    ]

    return DashboardSummary(
        tenant_id=tenant_id,
        total_sales=Decimal(str(total_sales)),
        total_amount_at_risk=fugas_report.total_amount_at_risk,
        top_risk_waiters=top_risk_waiters,
        top_dog_products=top_dog_products,
    )
