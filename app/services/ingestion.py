import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, Branch, Order, OrderItem, Staff
from app.schemas.order import ParrotOrderPayload, ParrotSyncPayload, SyncResultResponse


class ParrotIngestionService:
    """Ingests raw Parrot POS order payloads into the itable data model."""

    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def process_orders_payload(self, payload: ParrotSyncPayload) -> SyncResultResponse:
        orders_created = 0
        orders_skipped_duplicate = 0
        audit_events_created = 0
        branches_created = 0
        staff_created = 0

        for raw_order in payload.orders:
            if self._order_exists(raw_order.external_order_id):
                orders_skipped_duplicate += 1
                continue

            branch = None
            if raw_order.branch_external_id:
                branch, was_created = self._get_or_create_branch(
                    external_id=raw_order.branch_external_id,
                    name=raw_order.branch_name or raw_order.branch_external_id,
                )
                branches_created += int(was_created)

            staff = None
            if raw_order.staff_external_id:
                staff, was_created = self._get_or_create_staff(
                    external_id=raw_order.staff_external_id,
                    name=raw_order.staff_name or raw_order.staff_external_id,
                )
                staff_created += int(was_created)

            order = self._create_order(raw_order, branch_id=branch.id if branch else None,
                                        staff_id=staff.id if staff else None)
            orders_created += 1

            if self._requires_audit_event(raw_order):
                self._create_audit_event(order, raw_order, staff_id=staff.id if staff else None)
                audit_events_created += 1

        self.db.commit()

        return SyncResultResponse(
            orders_received=len(payload.orders),
            orders_created=orders_created,
            orders_skipped_duplicate=orders_skipped_duplicate,
            audit_events_created=audit_events_created,
            branches_created=branches_created,
            staff_created=staff_created,
        )

    def _order_exists(self, external_order_id: str) -> bool:
        stmt = select(Order.id).where(
            Order.tenant_id == self.tenant_id,
            Order.external_order_id == external_order_id,
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def _get_or_create_branch(self, external_id: str, name: str) -> tuple[Branch, bool]:
        stmt = select(Branch).where(
            Branch.tenant_id == self.tenant_id,
            Branch.external_id == external_id,
        )
        branch = self.db.execute(stmt).scalar_one_or_none()
        if branch is not None:
            return branch, False

        branch = Branch(tenant_id=self.tenant_id, external_id=external_id, name=name)
        self.db.add(branch)
        self.db.flush()
        return branch, True

    def _get_or_create_staff(self, external_id: str, name: str) -> tuple[Staff, bool]:
        stmt = select(Staff).where(
            Staff.tenant_id == self.tenant_id,
            Staff.external_id == external_id,
        )
        staff = self.db.execute(stmt).scalar_one_or_none()
        if staff is not None:
            return staff, False

        staff = Staff(tenant_id=self.tenant_id, external_id=external_id, name=name)
        self.db.add(staff)
        self.db.flush()
        return staff, True

    def _create_order(
        self,
        raw_order: ParrotOrderPayload,
        branch_id: uuid.UUID | None,
        staff_id: uuid.UUID | None,
    ) -> Order:
        order = Order(
            tenant_id=self.tenant_id,
            branch_id=branch_id,
            staff_id=staff_id,
            external_order_id=raw_order.external_order_id,
            table_name=raw_order.table_name,
            total_amount=raw_order.total_amount,
            discount_amount=raw_order.discount_amount,
            payment_method=raw_order.payment_method,
            status=raw_order.status,
            order_date=raw_order.order_date,
        )
        self.db.add(order)
        self.db.flush()

        for raw_item in raw_order.items:
            item = OrderItem(
                order_id=order.id,
                external_product_id=raw_item.external_product_id,
                product_name=raw_item.product_name,
                category_name=raw_item.category_name,
                quantity=raw_item.quantity,
                unit_price=raw_item.unit_price,
                unit_cost=raw_item.unit_cost,
                subtotal=raw_item.subtotal,
            )
            self.db.add(item)

        return order

    @staticmethod
    def _requires_audit_event(raw_order: ParrotOrderPayload) -> bool:
        return raw_order.status == "CANCELLED" or raw_order.discount_amount > 0

    def _create_audit_event(
        self,
        order: Order,
        raw_order: ParrotOrderPayload,
        staff_id: uuid.UUID | None,
    ) -> AuditEvent:
        if raw_order.status == "CANCELLED":
            event_type = "CANCELLED_ORDER"
            amount = raw_order.total_amount
            reason = "Orden cancelada en el POS"
        else:
            event_type = "DISCOUNT"
            amount = raw_order.discount_amount
            reason = raw_order.discount_reason or "Descuento aplicado a la orden"

        event = AuditEvent(
            tenant_id=self.tenant_id,
            order_id=order.id,
            staff_id=staff_id,
            event_type=event_type,
            amount=amount,
            reason=reason,
            event_time=raw_order.order_date,
        )
        self.db.add(event)
        self.db.flush()
        return event
