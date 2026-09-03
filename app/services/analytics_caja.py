import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CashShift, Staff
from app.schemas.analytics import CajaAuditReport, CashierDiscrepancySummary


@dataclass
class _CashierAccumulator:
    staff_id: uuid.UUID | None
    staff_name: str
    shifts_count: int = 0
    total_expected_cash: Decimal = Decimal("0")
    total_actual_cash: Decimal = Decimal("0")
    accumulated_discrepancy: Decimal = Decimal("0")


class CajaAnalyticsEngine:
    """Accumulates cash-register discrepancies per cashier to surface micro-mermas."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def analyze_cashier_discrepancies(self) -> CajaAuditReport:
        accumulators = self._aggregate_shifts_by_staff()

        cashiers: list[CashierDiscrepancySummary] = []
        total_accumulated = Decimal("0")

        for acc in accumulators.values():
            average_discrepancy = (
                acc.accumulated_discrepancy / acc.shifts_count
                if acc.shifts_count
                else Decimal("0")
            )
            total_accumulated += acc.accumulated_discrepancy

            cashiers.append(
                CashierDiscrepancySummary(
                    staff_id=acc.staff_id,
                    staff_name=acc.staff_name,
                    shifts_count=acc.shifts_count,
                    total_expected_cash=acc.total_expected_cash,
                    total_actual_cash=acc.total_actual_cash,
                    accumulated_discrepancy=acc.accumulated_discrepancy,
                    average_discrepancy=average_discrepancy,
                )
            )

        cashiers.sort(key=lambda c: abs(c.accumulated_discrepancy), reverse=True)

        return CajaAuditReport(
            tenant_id=self.tenant_id,
            total_accumulated_discrepancy=total_accumulated,
            cashiers=cashiers,
        )

    def _aggregate_shifts_by_staff(self) -> dict[uuid.UUID | None, _CashierAccumulator]:
        stmt = (
            select(CashShift, Staff)
            .outerjoin(Staff, CashShift.staff_id == Staff.id)
            .where(CashShift.tenant_id == self.tenant_id)
        )
        rows = self.db.execute(stmt).all()

        accumulators: dict[uuid.UUID | None, _CashierAccumulator] = defaultdict(
            lambda: _CashierAccumulator(staff_id=None, staff_name="Sin asignar")
        )

        for shift, staff in rows:
            key = shift.staff_id
            if key not in accumulators:
                accumulators[key] = _CashierAccumulator(
                    staff_id=shift.staff_id,
                    staff_name=staff.name if staff else "Sin asignar",
                )

            acc = accumulators[key]
            acc.shifts_count += 1
            acc.total_expected_cash += shift.expected_cash
            acc.total_actual_cash += shift.actual_cash
            acc.accumulated_discrepancy += shift.discrepancy

        return accumulators
