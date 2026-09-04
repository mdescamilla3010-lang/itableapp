"""Seed a tenant with realistic demo data so the itable app dashboards and
audits have something to show, without needing a real POS connection yet.

Generates ~3 weeks of orders (with a mix of normal and suspicious waiter
behavior), plus cash-register shifts (with one cashier showing a recurring
shortage pattern), and pushes them through the same /sync endpoints a real
POS integration would use.

Usage:
    python scripts/seed_demo_data.py \\
        --base-url https://itableapp-production.up.railway.app \\
        --tenant-slug cafe-escamilla

    # or, if you already know the tenant UUID:
    python scripts/seed_demo_data.py \\
        --base-url https://itableapp-production.up.railway.app \\
        --tenant-id 3f1b2c...
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import requests

WAITERS = [
    ("mesero-1", "Ana Torres"),
    ("mesero-2", "Luis Ramirez"),
    ("mesero-3", "Karla Jimenez"),
    ("mesero-4", "Diego Morales"),
    ("mesero-5", "Roberto Vega"),  # will show suspicious cancellation/discount behavior
    ("mesero-6", "Sofia Herrera"),
    ("mesero-7", "Andres Paredes"),
]

CASHIERS = [
    ("cajero-1", "Fernanda Ruiz"),
    ("cajero-2", "Miguel Soto"),  # will show a recurring cash shortage pattern
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


def build_orders(days: int, orders_per_day: tuple[int, int], seed: int) -> list[dict]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    orders: list[dict] = []
    order_seq = 0

    waiter_weights = [3, 3, 3, 3, 1.2, 3, 3]  # Roberto Vega gets fewer tables overall

    for day_offset in range(days, 0, -1):
        day = now - timedelta(days=day_offset)
        num_orders = rng.randint(*orders_per_day)

        for _ in range(num_orders):
            order_seq += 1
            waiter = rng.choices(WAITERS, weights=waiter_weights, k=1)[0]
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

            items = []
            chosen = rng.choices(MENU, weights=[m[5] for m in MENU], k=num_items)
            subtotal = Decimal("0")
            for external_id, name, category, price, cost, _weight in chosen:
                qty = rng.randint(*qty_range)
                items.append(
                    {
                        "external_product_id": external_id,
                        "product_name": name,
                        "category_name": category,
                        "quantity": qty,
                        "unit_price": price,
                        "unit_cost": cost,
                    }
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
                {
                    "external_order_id": f"demo-order-{order_seq}",
                    "branch_external_id": "sucursal-centro",
                    "branch_name": "Sucursal Centro",
                    "staff_external_id": waiter[0],
                    "staff_name": waiter[1],
                    "table_name": f"Mesa {rng.randint(1, 18)}",
                    "total_amount": str(total_amount),
                    "discount_amount": str(discount_amount),
                    "discount_reason": discount_reason,
                    "payment_method": rng.choice(PAYMENT_METHODS),
                    "status": status,
                    "order_date": order_time.isoformat(),
                    "items": items,
                }
            )

    return orders


def build_cash_shifts(days: int, seed: int) -> list[dict]:
    rng = random.Random(seed + 1)
    now = datetime.now(timezone.utc)
    shifts: list[dict] = []
    shift_seq = 0

    for day_offset in range(days, 0, -2):  # roughly one shift every other day per cashier
        day = now - timedelta(days=day_offset)

        for external_id, name in CASHIERS:
            shift_seq += 1
            is_suspect = name == "Miguel Soto"

            expected = Decimal(rng.randint(2200, 5800))
            if is_suspect:
                shortage = Decimal(rng.randint(80, 230))
                actual = expected - shortage
            else:
                noise = Decimal(rng.randint(-40, 40))
                actual = expected + noise

            start = day.replace(hour=12, minute=0, second=0, microsecond=0)
            end = day.replace(hour=20, minute=0, second=0, microsecond=0)

            shifts.append(
                {
                    "external_shift_id": f"demo-shift-{shift_seq}",
                    "staff_external_id": external_id,
                    "staff_name": name,
                    "expected_cash": str(expected),
                    "actual_cash": str(actual),
                    "shift_start": start.isoformat(),
                    "shift_end": end.isoformat(),
                }
            )

    return shifts


def resolve_tenant_id(base_url: str, tenant_slug: str) -> str:
    resp = requests.get(f"{base_url}/api/v1/tenants", timeout=30)
    resp.raise_for_status()
    for tenant in resp.json():
        if tenant["slug"] == tenant_slug:
            return tenant["id"]
    raise SystemExit(f"No se encontro ningun tenant con slug '{tenant_slug}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", required=True, help="URL base del backend, sin /api/v1 (ej. https://itableapp-production.up.railway.app)")
    tenant_group = parser.add_mutually_exclusive_group(required=True)
    tenant_group.add_argument("--tenant-id", help="UUID del tenant a poblar")
    tenant_group.add_argument("--tenant-slug", help="Slug del tenant a poblar (se resuelve via GET /tenants)")
    parser.add_argument("--days", type=int, default=21, help="Dias hacia atras a simular (default: 21)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    tenant_id = args.tenant_id or resolve_tenant_id(base_url, args.tenant_slug)

    orders = build_orders(days=args.days, orders_per_day=(14, 24), seed=args.seed)
    shifts = build_cash_shifts(days=args.days, seed=args.seed)

    print(f"Tenant: {tenant_id}")
    print(f"Generando {len(orders)} ordenes y {len(shifts)} turnos de caja...")

    orders_resp = requests.post(f"{base_url}/api/v1/sync/{tenant_id}", json={"orders": orders}, timeout=120)
    orders_resp.raise_for_status()
    print("Ordenes:", orders_resp.json())

    shifts_resp = requests.post(
        f"{base_url}/api/v1/sync/{tenant_id}/cash-shifts", json={"shifts": shifts}, timeout=120
    )
    shifts_resp.raise_for_status()
    print("Turnos de caja:", shifts_resp.json())

    print("\nListo. Recarga el Dashboard en el frontend para ver los numeros.")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"Error HTTP: {exc.response.status_code} - {exc.response.text}", file=sys.stderr)
        sys.exit(1)
