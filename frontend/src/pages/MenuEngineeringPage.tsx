import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { analyticsApi } from "../api/analytics";
import { Card } from "../components/ui/Card";
import { BranchSelector } from "../components/ui/BranchSelector";
import { EmptyState } from "../components/ui/EmptyState";
import { MenuCategoryPill } from "../components/ui/MenuCategoryPill";
import { PageHeader } from "../components/ui/PageHeader";
import { QueryState } from "../components/ui/QueryState";
import { StatTile } from "../components/ui/StatTile";
import { useTenantContext } from "../context/useTenantContext";
import type { MenuCategory, MenuItemAnalysis } from "../api/types";
import { MENU_CATEGORY_DESCRIPTIONS, MENU_CATEGORY_LABELS } from "../lib/labels";
import { formatCurrency, formatNumber } from "../lib/format";

const QUADRANT_ORDER: MenuCategory[] = ["ESTRELLA", "CABALLO_DE_BATALLA", "PUZZLE", "PERRO"];

const QUADRANT_CLASS: Record<MenuCategory, string> = {
  ESTRELLA: "pill--success",
  CABALLO_DE_BATALLA: "pill--primary",
  PUZZLE: "pill--warning",
  PERRO: "pill--danger",
};

function countByCategory(items: MenuItemAnalysis[]) {
  const counts: Record<MenuCategory, number> = {
    ESTRELLA: 0,
    CABALLO_DE_BATALLA: 0,
    PUZZLE: 0,
    PERRO: 0,
  };
  for (const item of items) counts[item.menu_category] += 1;
  return counts;
}

export function MenuEngineeringPage() {
  const { currentTenantId } = useTenantContext();
  const tenantId = currentTenantId as string;
  const [branchId, setBranchId] = useState<string | null>(null);

  const menuQuery = useQuery({
    queryKey: ["menu-engineering", tenantId, branchId],
    queryFn: () => analyticsApi.menuEngineering(tenantId, branchId),
  });

  return (
    <>
      <PageHeader
        title="Ingeniería de menú"
        description="Matriz de Kasavana & Smith: popularidad de venta vs. margen de ganancia por platillo."
        action={<BranchSelector tenantId={tenantId} value={branchId} onChange={setBranchId} />}
      />

      <QueryState {...menuQuery} loadingLabel="Clasificando platillos…">
        {(report) => {
          const counts = countByCategory(report.items);
          return (
            <>
              <div className="grid grid--stats">
                <StatTile label="Margen promedio por unidad" value={formatCurrency(report.avg_margin)} />
                <StatTile label="Volumen promedio vendido" value={formatNumber(report.avg_quantity_sold, 1)} />
              </div>

              <Card title="Distribución por cuadrante">
                <div className="quadrant-grid">
                  {QUADRANT_ORDER.map((category) => (
                    <div key={category} className={`quadrant pill ${QUADRANT_CLASS[category]}`}>
                      <span className="quadrant__count">{counts[category]}</span>
                      <span className="quadrant__label">{MENU_CATEGORY_LABELS[category]}</span>
                      <span className="quadrant__hint">{MENU_CATEGORY_DESCRIPTIONS[category]}</span>
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Platillos" subtitle="Ordenados por margen total descendente">
                {report.items.length === 0 ? (
                  <EmptyState
                    title="Sin ventas registradas"
                    description="Sincroniza órdenes completadas con productos para ver la matriz de menú."
                  />
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Platillo</th>
                          <th>Categoría (POS)</th>
                          <th className="text-right">Vendidos</th>
                          <th className="text-right">Precio prom.</th>
                          <th className="text-right">Costo prom.</th>
                          <th className="text-right">Margen unit.</th>
                          <th className="text-right">Margen total</th>
                          <th>Clasificación</th>
                          <th>Recomendación</th>
                        </tr>
                      </thead>
                      <tbody>
                        {report.items.map((item) => (
                          <tr key={item.external_product_id}>
                            <td>{item.product_name}</td>
                            <td className="text-muted">{item.category_name ?? "—"}</td>
                            <td className="text-right">{item.quantity_sold}</td>
                            <td className="text-right">{formatCurrency(item.avg_price)}</td>
                            <td className="text-right">{formatCurrency(item.avg_cost)}</td>
                            <td className="text-right">{formatCurrency(item.unit_margin)}</td>
                            <td className="text-right">{formatCurrency(item.total_margin)}</td>
                            <td>
                              <MenuCategoryPill category={item.menu_category} />
                            </td>
                            <td className="text-muted" style={{ whiteSpace: "normal", minWidth: "220px" }}>
                              {item.recommendation}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </>
          );
        }}
      </QueryState>
    </>
  );
}
