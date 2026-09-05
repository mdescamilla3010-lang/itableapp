"""Generates realistic demo data (orders, staff, cash shifts) for a tenant so
the dashboards and audit engines have something to show before a real POS
integration is connected. Used by the /sync/{tenant_id}/demo-data endpoint.
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.schemas.cash_shift import ParrotCashShiftPayload, ParrotCashShiftSyncPayload
from app.schemas.order import ParrotOrderItemPayload, ParrotOrderPayload, ParrotSyncPayload

WAITERS = [
    ("mesero-1", "Ana Torres"),
    ("mesero-2", "Luis Ramirez"),
    ("mesero-3", "Karla Jimenez"),
    ("mesero-4", "Diego Morales"),
    ("mesero-5", "Roberto Vega"),  # deliberately suspicious cancellation/discount pattern
    ("mesero-6", "Sofia Herrera"),
    ("mesero-7", "Andres Paredes"),
]
_WAITER_WEIGHTS = [3, 3, 3, 3, 1.2, 3, 3]

CASHIERS = [
    ("cajero-1", "Fernanda Ruiz"),
    ("cajero-2", "Miguel Soto"),  # deliberately recurring cash shortage
]

# (external_id, name, category, price, cost, sampling_weight)
MENU = [
    ("prod-01", "Hamburguesa Clasica", "Platos fuertes", 145, 55, 9),
    ("prod-02", "Alitas BBQ", "Entradas", 130, 48, 8),
    ("prod-03", "Filete Wagyu", "Platos fuertes", 420, 150, 2),
    ("prod-04", "Papas a la Francesa", "Entradas", 55, 30, 10),
    ("prod-05", "Ensalada Cesar", "Entradas", 90, 55, 6),
    ("prod-06", "Refresco", "Bebidas", 35, 20, 10),
    ("prod-07", "Tartara de Atun", "Entradas", 210, 70, 2),
    ("prod-08", "Costillas BBQ", "Platos fuertes", 260, 90, 3),
    ("prod-09", "Sopa del Dia", "Entradas", 60, 42, 2),
    ("prod-10", "Pay de Limon", "Postres", 70, 50, 2),
    ("prod-11", "Limonada", "Bebidas", 40, 22, 7),
    ("prod-12", "Cafe Americano", "Bebidas", 30, 12, 8),
]

PAYMENT_METHODS = ["CASH", "CARD", "CARD", "CARD"]


def _build_orders(days: int, orders_per_day: tuple[int, int], seed: int) -> list[ParrotOrderPayload]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    orders: list[ParrotOrderPayload] = []
    order_seq = 0

    for day_offset in range(days, 0, -1):
        day = now - timedelta(days=day_offset)
        num_orders = rng.randint(*orders_per_day)

        for _ in range(num_orders):
            order_seq += 1
            waiter = rng.choices(WAITERS, weights=_WAITER_WEIGHTS, k=1)[0]
            is_roberto = waiter[1] == "Roberto Vega"

            order_time = day.replace(
                hour=rng.randint(12, 22), minute=rng.randint(0, 59), second=0, microsecond=0
            )

            cancel_chance = 0.45 if is_roberto else 0.008
            discount_chance = 0.40 if is_roberto else 0.06
            status = "CANCELLED" if rng.random() < cancel_chance else "COMPLETED"

            # A waiter padding cancelled tickets tends to ring up bigger orders before voiding them.
            num_items = rng.randint(2, 3) if (is_roberto and status == "CANCELLED") else rng.randint(1, 3)
            qty_range = (3, 4) if (is_roberto and status == "CANCELLED") else (1, 2)

            items: list[ParrotOrderItemPayload] = []
            chosen = rng.choices(MENU, weights=[m[5] for m in MENU], k=num_items)
            subtotal = Decimal("0")
            for external_id, name, category, price, cost, _weight in chosen:
                qty = rng.randint(*qty_range)
                items.append(
                    ParrotOrderItemPayload(
                        external_product_id=external_id,
                        product_name=name,
                        category_name=category,
                        quantity=qty,
                        unit_price=Decimal(price),
                        unit_cost=Decimal(cost),
                    )
                )
                subtotal += Decimal(price) * qty

            discount_amount = Decimal("0")
            discount_reason = None
            if status != "CANCELLED" and rng.random() < discount_chance:
                pct = rng.uniform(0.20, 0.35) if is_roberto else rng.uniform(0.05, 0.12)
                discount_amount = (subtotal * Decimal(str(round(pct, 2)))).quantize(Decimal("0.01"))
                discount_reason = "Cortesia cliente frecuente" if is_roberto else "Promocion del dia"

            total_amount = subtotal - discount_amount
            if total_amount < 0:
                total_amount = Decimal("0")

            orders.append(
                ParrotOrderPayload(
                    external_order_id=f"demo-order-{order_seq}",
                    branch_external_id="sucursal-centro",
                    branch_name="Sucursal Centro",
                    staff_external_id=waiter[0],
                    staff_name=waiter[1],
                    table_name=f"Mesa {rng.randint(1, 18)}",
                    total_amount=total_amount,
                    discount_amount=discount_amount,
                    discount_reason=discount_reason,
                    payment_method=rng.choice(PAYMENT_METHODS),
                    status=status,
                    order_date=order_time,
                    items=items,
                )
            )

    return orders


def _build_cash_shifts(days: int, seed: int) -> list[ParrotCashShiftPayload]:
    rng = random.Random(seed + 1)
    now = datetime.now(timezone.utc)
    shifts: list[ParrotCashShiftPayload] = []
    shift_seq = 0

    for day_offset in range(days, 0, -2):  # roughly one shift every other day per cashier
        day = now - timedelta(days=day_offset)

        for external_id, name in CASHIERS:
            shift_seq += 1
            is_suspect = name == "Miguel Soto"

            expected = Decimal(rng.randint(2200, 5800))
            if is_suspect:
                actual = expected - Decimal(rng.randint(80, 230))
            else:
                actual = expected + Decimal(rng.randint(-40, 40))

            shifts.append(
                ParrotCashShiftPayload(
                    external_shift_id=f"demo-shift-{shift_seq}",
                    staff_external_id=external_id,
                    staff_name=name,
                    expected_cash=expected,
                    actual_cash=actual,
                    shift_start=day.replace(hour=12, minute=0, second=0, microsecond=0),
                    shift_end=day.replace(hour=20, minute=0, second=0, microsecond=0),
                )
            )

    return shifts


def generate_demo_orders_payload(days: int = 21, seed: int = 42) -> ParrotSyncPayload:
    return ParrotSyncPayload(orders=_build_orders(days=days, orders_per_day=(14, 24), seed=seed))


def generate_demo_cash_shifts_payload(days: int = 21, seed: int = 42) -> ParrotCashShiftSyncPayload:
    return ParrotCashShiftSyncPayload(shifts=_build_cash_shifts(days=days, seed=seed))
