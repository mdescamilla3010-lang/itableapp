import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Order, OrderItem
from app.schemas.analytics import MenuCategory, MenuEngineeringReport, MenuItemAnalysis

_RECOMMENDATIONS: dict[MenuCategory, str] = {
    MenuCategory.ESTRELLA: "Mantener calidad y visibilidad destacada en el menu; es tu mejor activo.",
    MenuCategory.CABALLO_DE_BATALLA: "Subir precio gradualmente o reducir costo de insumos sin afectar percepcion.",
    MenuCategory.PUZZLE: "Promocionar activamente (sugerencia del mesero, ubicacion privilegiada en menu).",
    MenuCategory.PERRO: "Quitar del menu o rediseñar por completo; consume espacio y margen sin retorno.",
}


@dataclass
class _ProductAccumulator:
    external_product_id: str
    product_name: str
    category_name: str | None
    quantity_sold: int = 0
    total_price: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    price_samples: int = 0
    total_margin: Decimal = Decimal("0")


class MenuEngineeringEngine:
    """Classifies menu items using the Kasavana & Smith engineering matrix."""

    def __init__(self, db: Session, tenant_id: uuid.UUID, branch_id: uuid.UUID | None = None) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.branch_id = branch_id

    def analyze_menu(self) -> MenuEngineeringReport:
        accumulators = self._aggregate_items_by_product()

        if not accumulators:
            return MenuEngineeringReport(tenant_id=self.tenant_id, avg_margin=0.0, avg_quantity_sold=0.0, items=[])

        margins = np.array(
            [float(acc.total_margin / acc.quantity_sold) for acc in accumulators.values() if acc.quantity_sold],
            dtype=float,
        )
        quantities = np.array(
            [acc.quantity_sold for acc in accumulators.values()], dtype=float
        )

        avg_margin = float(np.mean(margins)) if margins.size else 0.0
        avg_quantity = float(np.mean(quantities)) if quantities.size else 0.0

        items: list[MenuItemAnalysis] = []
        for acc in accumulators.values():
            if acc.quantity_sold == 0:
                continue

            avg_price = acc.total_price / acc.price_samples if acc.price_samples else Decimal("0")
            avg_cost = acc.total_cost / acc.price_samples if acc.price_samples else Decimal("0")
            unit_margin = avg_price - avg_cost
            popularity_index = acc.quantity_sold / avg_quantity if avg_quantity else 0.0

            category = self._classify(
                unit_margin=float(unit_margin),
                avg_margin=avg_margin,
                quantity_sold=acc.quantity_sold,
                avg_quantity=avg_quantity,
            )

            items.append(
                MenuItemAnalysis(
                    external_product_id=acc.external_product_id,
                    product_name=acc.product_name,
                    category_name=acc.category_name,
                    quantity_sold=acc.quantity_sold,
                    avg_price=avg_price,
                    avg_cost=avg_cost,
                    unit_margin=unit_margin,
                    total_margin=acc.total_margin,
                    popularity_index=round(popularity_index, 4),
                    menu_category=category,
                    recommendation=_RECOMMENDATIONS[category],
                )
            )

        items.sort(key=lambda i: i.total_margin, reverse=True)

        return MenuEngineeringReport(
            tenant_id=self.tenant_id,
            avg_margin=round(avg_margin, 4),
            avg_quantity_sold=round(avg_quantity, 4),
            items=items,
        )

    def _aggregate_items_by_product(self) -> dict[str, _ProductAccumulator]:
        stmt = (
            select(OrderItem)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.tenant_id == self.tenant_id, Order.status != "CANCELLED")
        )
        if self.branch_id is not None:
            stmt = stmt.where(Order.branch_id == self.branch_id)
        items = self.db.execute(stmt).scalars().all()

        accumulators: dict[str, _ProductAccumulator] = {}
        for item in items:
            key = item.external_product_id
            if key not in accumulators:
                accumulators[key] = _ProductAccumulator(
                    external_product_id=item.external_product_id,
                    product_name=item.product_name,
                    category_name=item.category_name,
                )

            acc = accumulators[key]
            acc.quantity_sold += item.quantity
            acc.total_price += item.unit_price
            acc.total_cost += item.unit_cost
            acc.price_samples += 1
            acc.total_margin += (item.unit_price - item.unit_cost) * item.quantity

        return accumulators

    @staticmethod
    def _classify(
        unit_margin: float,
        avg_margin: float,
        quantity_sold: int,
        avg_quantity: float,
    ) -> MenuCategory:
        high_margin = unit_margin >= avg_margin
        high_volume = quantity_sold >= avg_quantity

        if high_margin and high_volume:
            return MenuCategory.ESTRELLA
        if not high_margin and high_volume:
            return MenuCategory.CABALLO_DE_BATALLA
        if high_margin and not high_volume:
            return MenuCategory.PUZZLE
        return MenuCategory.PERRO
