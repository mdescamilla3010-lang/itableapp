import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { analyticsApi } from "../api/analytics";
import { Card } from "../components/ui/Card";
import { BranchSelector } from "../components/ui/BranchSelector";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
import { QueryState } from "../components/ui/QueryState";
import { RiskPill } from "../components/ui/RiskPill";
import { StatTile } from "../components/ui/StatTile";
import { useTenantContext } from "../context/useTenantContext";
import { formatCurrency, formatNumber } from "../lib/format";

export function DashboardPage() {
  const { currentTenantId } = useTenantContext();
  const tenantId = currentTenantId as string;
  const [branchId, setBranchId] = useState<string | null>(null);

  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary", tenantId, branchId],
    queryFn: () => analyticsApi.dashboardSummary(tenantId, branchId),
  });

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="KPIs ejecutivos consolidados de ventas, fugas de personal y desempeño de menú."
        action={<BranchSelector tenantId={tenantId} value={branchId} onChange={setBranchId} />}
      />

      <QueryState {...summaryQuery} loadingLabel="Calculando KPIs…">
        {(summary) => (
          <>
            <div className="grid grid--stats">
              <StatTile label="Ventas totales" value={formatCurrency(summary.total_sales)} />
              <StatTile
                label="Dinero total en riesgo"
                value={formatCurrency(summary.total_amount_at_risk)}
                danger={Number(summary.total_amount_at_risk) > 0}
                hint="Cancelaciones y descuentos con riesgo medio/alto"
              />
            </div>

            <div className="grid grid--two">
              <Card
                title="Top meseros en riesgo"
                subtitle="Mayor Z-Score de cancelaciones"
                action={
                  <Link to="/staff-audit" className="btn btn--ghost">
                    Ver todo
                  </Link>
                }
              >
                {summary.top_risk_waiters.length === 0 ? (
                  <EmptyState
                    title="Sin alertas de personal"
                    description="Sincroniza órdenes para ver auditoría de meseros."
                  />
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Mesero</th>
                          <th className="text-right">Z-Score</th>
                          <th className="text-right">Monto cancelado</th>
                          <th>Riesgo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.top_risk_waiters.map((w) => (
                          <tr key={w.staff_name}>
                            <td>{w.staff_name}</td>
                            <td className="text-right mono">{formatNumber(w.zscore, 2)}</td>
                            <td className="text-right">{formatCurrency(w.total_cancelled_amount)}</td>
                            <td>
                              <RiskPill level={w.risk_level} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>

              <Card
                title="Productos a eliminar"
                subtitle="Top 'Perro' en la matriz de ingeniería de menú"
                action={
                  <Link to="/menu-engineering" className="btn btn--ghost">
                    Ver todo
                  </Link>
                }
              >
                {summary.top_dog_products.length === 0 ? (
                  <EmptyState
                    title="Sin productos en riesgo"
                    description="Sincroniza órdenes para ver la matriz de menú."
                  />
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Producto</th>
                          <th className="text-right">Vendidos</th>
                          <th className="text-right">Margen unitario</th>
                        </tr>
                      </thead>
                      <tbody>
                        {summary.top_dog_products.map((p) => (
                          <tr key={p.product_name}>
                            <td>{p.product_name}</td>
                            <td className="text-right">{p.quantity_sold}</td>
                            <td className="text-right">{formatCurrency(p.unit_margin)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>
          </>
        )}
      </QueryState>
    </>
  );
}
