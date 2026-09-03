import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AuditEvent, Staff
from app.schemas.analytics import FugasAuditReport, RiskLevel, WaiterAnomaly


@dataclass
class _WaiterAccumulator:
    staff_id: uuid.UUID | None
    staff_name: str
    cancellations_count: int = 0
    cancelled_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")


class FugasAnalyticsEngine:
    """Detects abnormal cancellation/discount behavior per waiter using Z-Score."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def analyze_waiter_anomalies(self) -> FugasAuditReport:
        accumulators = self._aggregate_events_by_staff()

        cancelled_amounts = np.array(
            [float(acc.cancelled_amount) for acc in accumulators.values()], dtype=float
        )

        mean = float(np.mean(cancelled_amounts)) if cancelled_amounts.size else 0.0
        std = float(np.std(cancelled_amounts)) if cancelled_amounts.size else 0.0

        waiters: list[WaiterAnomaly] = []
        total_at_risk = Decimal("0")

        for acc in accumulators.values():
            zscore = self._compute_zscore(float(acc.cancelled_amount), mean, std)
            risk_level = self._classify_risk(zscore, acc.cancelled_amount)

            if risk_level in (RiskLevel.HIGH_RISK, RiskLevel.MEDIUM_RISK):
                total_at_risk += acc.cancelled_amount + acc.discount_amount

            waiters.append(
                WaiterAnomaly(
                    staff_id=acc.staff_id,
                    staff_name=acc.staff_name,
                    total_cancellations_count=acc.cancellations_count,
                    total_cancelled_amount=acc.cancelled_amount,
                    total_discount_amount=acc.discount_amount,
                    zscore=round(zscore, 4),
                    risk_level=risk_level,
                )
            )

        waiters.sort(key=lambda w: w.zscore, reverse=True)

        return FugasAuditReport(
            tenant_id=self.tenant_id,
            total_amount_at_risk=total_at_risk,
            restaurant_mean_cancelled=round(mean, 4),
            restaurant_std_cancelled=round(std, 4),
            waiters=waiters,
        )

    def _aggregate_events_by_staff(self) -> dict[uuid.UUID | None, _WaiterAccumulator]:
        stmt = (
            select(AuditEvent, Staff)
            .outerjoin(Staff, AuditEvent.staff_id == Staff.id)
            .where(AuditEvent.tenant_id == self.tenant_id)
        )
        rows = self.db.execute(stmt).all()

        accumulators: dict[uuid.UUID | None, _WaiterAccumulator] = defaultdict(
            lambda: _WaiterAccumulator(staff_id=None, staff_name="Sin asignar")
        )

        for event, staff in rows:
            key = event.staff_id
            if key not in accumulators:
                accumulators[key] = _WaiterAccumulator(
                    staff_id=event.staff_id,
                    staff_name=staff.name if staff else "Sin asignar",
                )

            acc = accumulators[key]
            if event.event_type == "CANCELLED_ORDER":
                acc.cancellations_count += 1
                acc.cancelled_amount += event.amount
            elif event.event_type == "DISCOUNT":
                acc.discount_amount += event.amount

        return accumulators

    @staticmethod
    def _compute_zscore(value: float, mean: float, std: float) -> float:
        if std == 0:
            return 0.0
        return (value - mean) / std

    @staticmethod
    def _classify_risk(zscore: float, cancelled_amount: Decimal) -> RiskLevel:
        if zscore >= settings.FUGAS_ZSCORE_HIGH_RISK and cancelled_amount > Decimal(
            str(settings.FUGAS_HIGH_RISK_MIN_AMOUNT)
        ):
            return RiskLevel.HIGH_RISK
        if zscore >= settings.FUGAS_ZSCORE_MEDIUM_RISK:
            return RiskLevel.MEDIUM_RISK
        return RiskLevel.NORMAL
