from decimal import Decimal

from app.db.models import CashShift, Staff
from app.schemas.cash_shift import ParrotCashShiftSyncPayload
from app.services.ingestion import ParrotIngestionService


def _payload(**overrides):
    base = {
        "shifts": [
            {
                "external_shift_id": "SH-1",
                "staff_external_id": "C-1",
                "staff_name": "Ana Cajera",
                "expected_cash": "1000.00",
                "actual_cash": "950.00",
                "shift_start": "2026-01-01T08:00:00Z",
                "shift_end": "2026-01-01T16:00:00Z",
            }
        ]
    }
    base.update(overrides)
    return ParrotCashShiftSyncPayload.model_validate(base)


def test_process_cash_shifts_creates_staff_and_shift_with_discrepancy(db_session, tenant):
    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    result = service.process_cash_shifts_payload(_payload())

    assert result.shifts_created == 1
    assert result.staff_created == 1
    assert result.shifts_skipped_duplicate == 0

    shift = db_session.query(CashShift).filter(CashShift.tenant_id == tenant.id).one()
    assert shift.external_shift_id == "SH-1"
    assert shift.expected_cash == Decimal("1000.00")
    assert shift.actual_cash == Decimal("950.00")
    assert shift.discrepancy == Decimal("-50.00")

    assert db_session.query(Staff).filter(Staff.tenant_id == tenant.id).count() == 1


def test_process_cash_shifts_is_idempotent_on_external_shift_id(db_session, tenant):
    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    payload = _payload()

    first = service.process_cash_shifts_payload(payload)
    second = service.process_cash_shifts_payload(payload)

    assert first.shifts_created == 1
    assert second.shifts_created == 0
    assert second.shifts_skipped_duplicate == 1
    assert db_session.query(CashShift).filter(CashShift.tenant_id == tenant.id).count() == 1


def test_reuses_existing_staff_across_orders_and_cash_shifts(db_session, tenant):
    staff = Staff(tenant_id=tenant.id, external_id="C-1", name="Ana Cajera")
    db_session.add(staff)
    db_session.commit()

    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    result = service.process_cash_shifts_payload(_payload())

    assert result.staff_created == 0
    assert db_session.query(Staff).filter(Staff.tenant_id == tenant.id).count() == 1


def test_shift_without_staff_reference_is_allowed(db_session, tenant):
    payload = _payload(
        shifts=[
            {
                "external_shift_id": "SH-2",
                "expected_cash": "500.00",
                "actual_cash": "500.00",
                "shift_start": "2026-01-01T08:00:00Z",
            }
        ]
    )

    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    result = service.process_cash_shifts_payload(payload)

    assert result.shifts_created == 1
    shift = db_session.query(CashShift).filter(CashShift.tenant_id == tenant.id).one()
    assert shift.staff_id is None
    assert shift.discrepancy == Decimal("0.00")
