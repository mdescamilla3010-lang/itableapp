from decimal import Decimal

from app.db.models import AuditEvent, Branch, Order, Staff
from app.schemas.order import ParrotSyncPayload
from app.services.ingestion import ParrotIngestionService


def _payload(**overrides):
    base = {
        "orders": [
            {
                "external_order_id": "ORD-1",
                "branch_external_id": "BR-1",
                "branch_name": "Sucursal Centro",
                "staff_external_id": "W-1",
                "staff_name": "Juan Perez",
                "total_amount": "500.00",
                "discount_amount": "0",
                "status": "COMPLETED",
                "order_date": "2026-01-01T12:00:00Z",
                "items": [
                    {
                        "external_product_id": "P1",
                        "product_name": "Tacos",
                        "category_name": "Comida",
                        "quantity": 5,
                        "unit_price": "100.00",
                        "unit_cost": "40.00",
                    }
                ],
            }
        ]
    }
    base.update(overrides)
    return ParrotSyncPayload.model_validate(base)


def test_process_orders_creates_branch_staff_and_order(db_session, tenant):
    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    result = service.process_orders_payload(_payload())

    assert result.orders_created == 1
    assert result.branches_created == 1
    assert result.staff_created == 1
    assert result.audit_events_created == 0

    order = db_session.query(Order).filter(Order.tenant_id == tenant.id).one()
    assert order.external_order_id == "ORD-1"
    assert order.total_amount == Decimal("500.00")
    assert len(order.items) == 1

    assert db_session.query(Branch).filter(Branch.tenant_id == tenant.id).count() == 1
    assert db_session.query(Staff).filter(Staff.tenant_id == tenant.id).count() == 1


def test_process_orders_is_idempotent_on_external_order_id(db_session, tenant):
    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    payload = _payload()

    first = service.process_orders_payload(payload)
    second = service.process_orders_payload(payload)

    assert first.orders_created == 1
    assert second.orders_created == 0
    assert second.orders_skipped_duplicate == 1
    assert db_session.query(Order).filter(Order.tenant_id == tenant.id).count() == 1


def test_repeated_sync_does_not_duplicate_branch_or_staff(db_session, tenant):
    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    other_order_payload = _payload(
        orders=[
            {
                "external_order_id": "ORD-2",
                "branch_external_id": "BR-1",
                "branch_name": "Sucursal Centro",
                "staff_external_id": "W-1",
                "staff_name": "Juan Perez",
                "total_amount": "200.00",
                "discount_amount": "0",
                "status": "COMPLETED",
                "order_date": "2026-01-01T13:00:00Z",
                "items": [],
            }
        ]
    )

    service.process_orders_payload(_payload())
    result = service.process_orders_payload(other_order_payload)

    assert result.branches_created == 0
    assert result.staff_created == 0
    assert db_session.query(Branch).filter(Branch.tenant_id == tenant.id).count() == 1
    assert db_session.query(Staff).filter(Staff.tenant_id == tenant.id).count() == 1


def test_cancelled_order_creates_audit_event(db_session, tenant):
    payload = _payload(
        orders=[
            {
                "external_order_id": "ORD-3",
                "staff_external_id": "W-2",
                "staff_name": "Maria Lopez",
                "total_amount": "2000.00",
                "discount_amount": "0",
                "status": "CANCELLED",
                "order_date": "2026-01-01T14:00:00Z",
                "items": [],
            }
        ]
    )

    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    result = service.process_orders_payload(payload)

    assert result.audit_events_created == 1
    event = db_session.query(AuditEvent).filter(AuditEvent.tenant_id == tenant.id).one()
    assert event.event_type == "CANCELLED_ORDER"
    assert event.amount == Decimal("2000.00")


def test_discounted_order_creates_audit_event(db_session, tenant):
    payload = _payload(
        orders=[
            {
                "external_order_id": "ORD-4",
                "staff_external_id": "W-3",
                "staff_name": "Ana Torres",
                "total_amount": "400.00",
                "discount_amount": "100.00",
                "discount_reason": "Cliente frecuente",
                "status": "COMPLETED",
                "order_date": "2026-01-01T15:00:00Z",
                "items": [],
            }
        ]
    )

    service = ParrotIngestionService(db=db_session, tenant_id=tenant.id)
    result = service.process_orders_payload(payload)

    assert result.audit_events_created == 1
    event = db_session.query(AuditEvent).filter(AuditEvent.tenant_id == tenant.id).one()
    assert event.event_type == "DISCOUNT"
    assert event.amount == Decimal("100.00")
    assert event.reason == "Cliente frecuente"
