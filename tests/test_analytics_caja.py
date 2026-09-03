import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.db.models import CashShift, Staff
from app.services.analytics_caja import CajaAnalyticsEngine


def test_accumulates_discrepancy_per_cashier(db_session, tenant):
    staff = Staff(tenant_id=tenant.id, external_id=str(uuid.uuid4()), name="Cajero 1")
    db_session.add(staff)
    db_session.commit()
    db_session.refresh(staff)

    for expected, actual in [("1000.00", "950.00"), ("800.00", "770.00")]:
        shift = CashShift(
            tenant_id=tenant.id,
            staff_id=staff.id,
            external_shift_id=str(uuid.uuid4()),
            expected_cash=Decimal(expected),
            actual_cash=Decimal(actual),
            discrepancy=Decimal(actual) - Decimal(expected),
            shift_start=datetime(2026, 1, 1, 8, tzinfo=timezone.utc),
            shift_end=datetime(2026, 1, 1, 16, tzinfo=timezone.utc),
        )
        db_session.add(shift)
    db_session.commit()

    report = CajaAnalyticsEngine(db=db_session, tenant_id=tenant.id).analyze_cashier_discrepancies()

    assert len(report.cashiers) == 1
    cashier = report.cashiers[0]
    assert cashier.shifts_count == 2
    assert cashier.accumulated_discrepancy == Decimal("-80.00")
    assert cashier.average_discrepancy == Decimal("-40.00")
    assert report.total_accumulated_discrepancy == Decimal("-80.00")


def test_no_shifts_returns_empty_report(db_session, tenant):
    report = CajaAnalyticsEngine(db=db_session, tenant_id=tenant.id).analyze_cashier_discrepancies()
    assert report.cashiers == []
    assert report.total_accumulated_discrepancy == Decimal("0")
