import datetime
import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Order
from app.schemas.analytics import CashFlowProjection, DailyRevenue, FinancialDashboardReport

_PROJECTION_WINDOW_DAYS = 7


class FinancialAnalyticsEngine:
    """Ventas diarias y proyección simple de flujo de caja a partir del historial de ordenes."""

    def __init__(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        branch_id: uuid.UUID | None = None,
        period_days: int = 30,
    ) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.branch_id = branch_id
        self.period_days = period_days

    def analyze_financials(self) -> FinancialDashboardReport:
        today = datetime.datetime.now(datetime.UTC).date()
        period_start = today - datetime.timedelta(days=self.period_days - 1)
        previous_start = period_start - datetime.timedelta(days=self.period_days)

        current_by_day, current_orders = self._revenue_by_day(previous_start=period_start, end=today)
        previous_by_day, _ = self._revenue_by_day(previous_start=previous_start, end=period_start - datetime.timedelta(days=1))

        daily_revenue = [
            DailyRevenue(
                date=period_start + datetime.timedelta(days=offset),
                total_sales=current_by_day.get(period_start + datetime.timedelta(days=offset), Decimal("0")),
                order_count=current_orders.get(period_start + datetime.timedelta(days=offset), 0),
            )
            for offset in range(self.period_days)
        ]

        total_revenue = sum((day.total_sales for day in daily_revenue), Decimal("0"))
        total_order_count = sum(day.order_count for day in daily_revenue)
        avg_daily_revenue = total_revenue / self.period_days if self.period_days else Decimal("0")
        avg_ticket = total_revenue / total_order_count if total_order_count else Decimal("0")

        previous_total = sum(previous_by_day.values(), Decimal("0"))
        growth = self._growth_rate(current=total_revenue, previous=previous_total)

        projection = self._project_cash_flow(daily_revenue=daily_revenue, from_date=today)

        return FinancialDashboardReport(
            tenant_id=self.tenant_id,
            period_days=self.period_days,
            total_revenue=total_revenue,
            avg_daily_revenue=round(avg_daily_revenue, 2),
            avg_ticket=round(avg_ticket, 2),
            growth_vs_previous_period=growth,
            daily_revenue=daily_revenue,
            projection=projection,
        )

    def _revenue_by_day(
        self, previous_start: datetime.date, end: datetime.date
    ) -> tuple[dict[datetime.date, Decimal], dict[datetime.date, int]]:
        if previous_start > end:
            return {}, {}

        start_dt = datetime.datetime.combine(previous_start, datetime.time.min, tzinfo=datetime.UTC)
        end_dt = datetime.datetime.combine(end, datetime.time.max, tzinfo=datetime.UTC)

        stmt = select(Order).where(
            Order.tenant_id == self.tenant_id,
            Order.status != "CANCELLED",
            Order.order_date >= start_dt,
            Order.order_date <= end_dt,
        )
        if self.branch_id is not None:
            stmt = stmt.where(Order.branch_id == self.branch_id)

        orders = self.db.execute(stmt).scalars().all()

        revenue_by_day: dict[datetime.date, Decimal] = defaultdict(lambda: Decimal("0"))
        count_by_day: dict[datetime.date, int] = defaultdict(int)
        for order in orders:
            day = order.order_date.date()
            revenue_by_day[day] += order.total_amount - order.discount_amount
            count_by_day[day] += 1

        return dict(revenue_by_day), dict(count_by_day)

    @staticmethod
    def _growth_rate(current: Decimal, previous: Decimal) -> float | None:
        if previous == 0:
            return None
        return round(float((current - previous) / previous) * 100, 2)

    @staticmethod
    def _project_cash_flow(
        daily_revenue: list[DailyRevenue], from_date: datetime.date
    ) -> list[CashFlowProjection]:
        recent = daily_revenue[-_PROJECTION_WINDOW_DAYS:]
        if not recent:
            return []

        moving_average = sum((day.total_sales for day in recent), Decimal("0")) / len(recent)

        return [
            CashFlowProjection(
                date=from_date + datetime.timedelta(days=offset),
                projected_amount=round(moving_average, 2),
            )
            for offset in range(1, _PROJECTION_WINDOW_DAYS + 1)
        ]
