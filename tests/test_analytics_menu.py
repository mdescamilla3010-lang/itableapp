import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.db.models import Order, OrderItem
from app.schemas.analytics import MenuCategory
from app.services.analytics_menu import MenuEngineeringEngine


def _make_order_with_item(db_session, tenant, product_id, product_name, quantity, price, cost, status="COMPLETED"):
    order = Order(
        tenant_id=tenant.id,
        external_order_id=str(uuid.uuid4()),
        total_amount=Decimal(price) * quantity,
        discount_amount=Decimal("0"),
        status=status,
        order_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add(order)
    db_session.flush()

    item = OrderItem(
        order_id=order.id,
        external_product_id=product_id,
        product_name=product_name,
        category_name="Comida",
        quantity=quantity,
        unit_price=Decimal(price),
        unit_cost=Decimal(cost),
        subtotal=Decimal(price) * quantity,
    )
    db_session.add(item)
    db_session.commit()
    return order


def test_menu_engineering_classifies_star_and_dog(db_session, tenant):
    # High margin, high volume -> ESTRELLA
    _make_order_with_item(db_session, tenant, "P1", "Tacos", 20, "100.00", "30.00")
    # Low margin, low volume -> PERRO
    _make_order_with_item(db_session, tenant, "P2", "Sopa", 1, "50.00", "45.00")

    report = MenuEngineeringEngine(db=db_session, tenant_id=tenant.id).analyze_menu()

    by_id = {i.external_product_id: i for i in report.items}
    assert by_id["P1"].menu_category == MenuCategory.ESTRELLA
    assert by_id["P2"].menu_category == MenuCategory.PERRO
    assert by_id["P1"].recommendation
    assert by_id["P2"].recommendation


def test_cancelled_orders_are_excluded_from_menu_analysis(db_session, tenant):
    _make_order_with_item(db_session, tenant, "PX", "Cancelado", 1, "100.00", "10.00", status="CANCELLED")

    report = MenuEngineeringEngine(db=db_session, tenant_id=tenant.id).analyze_menu()
    assert report.items == []


def test_no_orders_returns_empty_report(db_session, tenant):
    report = MenuEngineeringEngine(db=db_session, tenant_id=tenant.id).analyze_menu()
    assert report.items == []
    assert report.avg_margin == 0.0
