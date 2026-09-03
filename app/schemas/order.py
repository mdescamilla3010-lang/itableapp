import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ParrotOrderItemPayload(BaseModel):
    """Raw shape of a single order line item as sent by Parrot POS."""

    external_product_id: str
    product_name: str
    category_name: str | None = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0")
    unit_cost: Decimal = Decimal("0")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class ParrotOrderPayload(BaseModel):
    """Raw shape of a single order as sent by Parrot POS."""

    external_order_id: str
    branch_external_id: str | None = None
    branch_name: str | None = None
    staff_external_id: str | None = None
    staff_name: str | None = None
    table_name: str | None = None
    total_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    discount_reason: str | None = None
    payment_method: str | None = None
    status: str = "COMPLETED"
    order_date: datetime
    items: list[ParrotOrderItemPayload] = Field(default_factory=list)


class ParrotSyncPayload(BaseModel):
    """Top-level payload accepted by the /sync endpoint."""

    orders: list[ParrotOrderPayload] = Field(default_factory=list)


class SyncResultResponse(BaseModel):
    orders_received: int
    orders_created: int
    orders_skipped_duplicate: int
    audit_events_created: int
    branches_created: int
    staff_created: int


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_product_id: str
    product_name: str
    category_name: str | None
    quantity: int
    unit_price: Decimal
    unit_cost: Decimal
    subtotal: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    branch_id: uuid.UUID | None
    staff_id: uuid.UUID | None
    external_order_id: str
    table_name: str | None
    total_amount: Decimal
    discount_amount: Decimal
    payment_method: str | None
    status: str
    order_date: datetime
    items: list[OrderItemRead] = Field(default_factory=list)
