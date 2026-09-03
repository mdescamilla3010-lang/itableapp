import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.db.models import AuditEvent, Staff
from app.schemas.analytics import RiskLevel
from app.services.analytics_fugas import FugasAnalyticsEngine


def _make_staff(db_session, tenant, name):
    staff = Staff(tenant_id=tenant.id, external_id=str(uuid.uuid4()), name=name)
    db_session.add(staff)
    db_session.commit()
    db_session.refresh(staff)
    return staff


def _make_cancel_event(db_session, tenant, staff, amount):
    event = AuditEvent(
        tenant_id=tenant.id,
        staff_id=staff.id,
        event_type="CANCELLED_ORDER",
        amount=Decimal(amount),
        reason="test",
        event_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(event)
    db_session.commit()


def test_high_risk_waiter_detected_by_zscore(db_session, tenant):
    # With n "normal" waiters at the same amount and one outlier, the
    # outlier's Z-Score converges to sqrt(n); n=5 keeps it comfortably
    # above the HIGH_RISK threshold of 2.0.
    normal_waiters = [_make_staff(db_session, tenant, f"Mesero Normal {i}") for i in range(5)]
    outlier = _make_staff(db_session, tenant, "Mesero Sospechoso")

    for staff in normal_waiters:
        _make_cancel_event(db_session, tenant, staff, "100.00")
    _make_cancel_event(db_session, tenant, outlier, "5000.00")

    report = FugasAnalyticsEngine(db=db_session, tenant_id=tenant.id).analyze_waiter_anomalies()

    by_name = {w.staff_name: w for w in report.waiters}
    assert by_name["Mesero Sospechoso"].risk_level == RiskLevel.HIGH_RISK
    assert by_name["Mesero Sospechoso"].zscore >= 2.0
    assert by_name["Mesero Normal 0"].risk_level == RiskLevel.NORMAL
    assert report.total_amount_at_risk >= Decimal("5000.00")


def test_medium_risk_waiter_below_amount_threshold(db_session, tenant):
    normal_waiters = [_make_staff(db_session, tenant, f"Mesero Normal {i}") for i in range(3)]
    borderline = _make_staff(db_session, tenant, "Mesero Borderline")

    for staff in normal_waiters:
        _make_cancel_event(db_session, tenant, staff, "50.00")
    # High relative to the group but under the $1,000 MXN high-risk floor.
    _make_cancel_event(db_session, tenant, borderline, "500.00")

    report = FugasAnalyticsEngine(db=db_session, tenant_id=tenant.id).analyze_waiter_anomalies()

    by_name = {w.staff_name: w for w in report.waiters}
    assert by_name["Mesero Borderline"].risk_level == RiskLevel.MEDIUM_RISK
    assert 1.0 <= by_name["Mesero Borderline"].zscore < 2.0


def test_no_events_returns_empty_report(db_session, tenant):
    report = FugasAnalyticsEngine(db=db_session, tenant_id=tenant.id).analyze_waiter_anomalies()
    assert report.waiters == []
    assert report.total_amount_at_risk == Decimal("0")
