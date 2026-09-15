import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.db.models import Order
from app.services.analytics_financial import FinancialAnalyticsEngine


def _make_order(db_session, tenant, total, days_ago, status="COMPLETED", discount="0"):
    order = Order(
        tenant_id=tenant.id,
        external_order_id=str(uuid.uuid4()),
        total_amount=Decimal(total),
        discount_amount=Decimal(discount),
        status=status,
        order_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )
    db_session.add(order)
    db_session.commit()
    return order


def test_financial_dashboard_aggregates_daily_revenue_and_growth(db_session, tenant):
    # Current period (period_days=2): today and yesterday.
    _make_order(db_session, tenant, "100.00", days_ago=0)
    _make_order(db_session, tenant, "50.00", days_ago=1)
    # Previous period: two and three days ago.
    _make_order(db_session, tenant, "40.00", days_ago=2)
    _make_order(db_session, tenant, "20.00", days_ago=3)

    report = FinancialAnalyticsEngine(db=db_session, tenant_id=tenant.id, period_days=2).analyze_financials()

    assert report.total_revenue == Decimal("150.00")
    assert report.avg_daily_revenue == Decimal("75.00")
    assert report.avg_ticket == Decimal("75.00")
    assert report.growth_vs_previous_period == 150.0
    assert len(report.daily_revenue) == 2
    assert sum(day.total_sales for day in report.daily_revenue) == Decimal("150.00")


def test_cancelled_orders_are_excluded_from_financial_dashboard(db_session, tenant):
    _make_order(db_session, tenant, "100.00", days_ago=0, status="CANCELLED")

    report = FinancialAnalyticsEngine(db=db_session, tenant_id=tenant.id, period_days=2).analyze_financials()

    assert report.total_revenue == Decimal("0")
    assert all(day.total_sales == Decimal("0") for day in report.daily_revenue)


def test_discount_is_subtracted_from_revenue(db_session, tenant):
    _make_order(db_session, tenant, "100.00", days_ago=0, discount="10.00")

    report = FinancialAnalyticsEngine(db=db_session, tenant_id=tenant.id, period_days=1).analyze_financials()

    assert report.total_revenue == Decimal("90.00")


def test_no_orders_returns_zeroed_report_with_projection_window(db_session, tenant):
    report = FinancialAnalyticsEngine(db=db_session, tenant_id=tenant.id, period_days=5).analyze_financials()

    assert report.total_revenue == Decimal("0")
    assert report.avg_ticket == Decimal("0")
    assert report.growth_vs_previous_period is None
    assert len(report.daily_revenue) == 5
    assert len(report.projection) == 7
    assert all(day.projected_amount == Decimal("0") for day in report.projection)


def test_projection_uses_moving_average_of_recent_days(db_session, tenant):
    _make_order(db_session, tenant, "100.00", days_ago=0)
    _make_order(db_session, tenant, "50.00", days_ago=1)

    report = FinancialAnalyticsEngine(db=db_session, tenant_id=tenant.id, period_days=2).analyze_financials()

    assert len(report.projection) == 7
    assert all(day.projected_amount == Decimal("75.00") for day in report.projection)
