import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ParrotCashShiftPayload(BaseModel):
    """Raw shape of a single cash-register shift as sent by Parrot POS."""

    external_shift_id: str
    staff_external_id: str | None = None
    staff_name: str | None = None
    expected_cash: Decimal = Decimal("0")
    actual_cash: Decimal = Decimal("0")
    shift_start: datetime
    shift_end: datetime | None = None


class ParrotCashShiftSyncPayload(BaseModel):
    """Top-level payload accepted by the /sync/{tenant_id}/cash-shifts endpoint."""

    shifts: list[ParrotCashShiftPayload] = Field(default_factory=list)


class CashShiftSyncResultResponse(BaseModel):
    shifts_received: int
    shifts_created: int
    shifts_skipped_duplicate: int
    staff_created: int


class CashShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    staff_id: uuid.UUID | None
    external_shift_id: str
    expected_cash: Decimal
    actual_cash: Decimal
    discrepancy: Decimal
    shift_start: datetime
    shift_end: datetime | None
