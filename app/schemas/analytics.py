import uuid
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    HIGH_RISK = "HIGH_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    NORMAL = "NORMAL"


class MenuCategory(StrEnum):
    ESTRELLA = "ESTRELLA"
    CABALLO_DE_BATALLA = "CABALLO_DE_BATALLA"
    PUZZLE = "PUZZLE"
    PERRO = "PERRO"


class WaiterAnomaly(BaseModel):
    staff_id: uuid.UUID | None
    staff_name: str
    total_cancellations_count: int
    total_cancelled_amount: Decimal
    total_discount_amount: Decimal
    zscore: float
    risk_level: RiskLevel


class FugasAuditReport(BaseModel):
    tenant_id: uuid.UUID
    total_amount_at_risk: Decimal
    restaurant_mean_cancelled: float
    restaurant_std_cancelled: float
    waiters: list[WaiterAnomaly] = Field(default_factory=list)


class CashierDiscrepancySummary(BaseModel):
    staff_id: uuid.UUID | None
    staff_name: str
    shifts_count: int
    total_expected_cash: Decimal
    total_actual_cash: Decimal
    accumulated_discrepancy: Decimal
    average_discrepancy: Decimal


class CajaAuditReport(BaseModel):
    tenant_id: uuid.UUID
    total_accumulated_discrepancy: Decimal
    cashiers: list[CashierDiscrepancySummary] = Field(default_factory=list)


class MenuItemAnalysis(BaseModel):
    external_product_id: str
    product_name: str
    category_name: str | None
    quantity_sold: int
    avg_price: Decimal
    avg_cost: Decimal
    unit_margin: Decimal
    total_margin: Decimal
    popularity_index: float
    menu_category: MenuCategory
    recommendation: str


class MenuEngineeringReport(BaseModel):
    tenant_id: uuid.UUID
    avg_margin: float
    avg_quantity_sold: float
    items: list[MenuItemAnalysis] = Field(default_factory=list)


class TopWaiterRisk(BaseModel):
    staff_name: str
    zscore: float
    total_cancelled_amount: Decimal
    risk_level: RiskLevel


class TopDogProduct(BaseModel):
    product_name: str
    quantity_sold: int
    unit_margin: Decimal


class DashboardSummary(BaseModel):
    tenant_id: uuid.UUID
    total_sales: Decimal
    total_amount_at_risk: Decimal
    top_risk_waiters: list[TopWaiterRisk] = Field(default_factory=list)
    top_dog_products: list[TopDogProduct] = Field(default_factory=list)
