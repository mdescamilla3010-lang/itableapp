import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { analyticsApi } from "../api/analytics";
import { Card } from "../components/ui/Card";
import { BranchSelector } from "../components/ui/BranchSelector";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
import { QueryState } from "../components/ui/QueryState";
import { StatTile } from "../components/ui/StatTile";
import { useTenantContext } from "../context/useTenantContext";
import type { CashFlowProjection, DailyRevenue } from "../api/types";
import { formatCurrency } from "../lib/format";

function formatShortDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short" }).format(date);
}

function formatLongDate(value: string): string {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "long" }).format(date);
}

function formatGrowth(value: number | null): string {
  if (value === null) return "Sin datos previos";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}% vs. periodo anterior`;
}

interface RevenueChartProps {
  history: DailyRevenue[];
  projection: CashFlowProjection[];
}

function RevenueChart({ history, projection }: RevenueChartProps) {
  const historyMax = Math.max(0, ...history.map((day) => Number(day.total_sales)));
  const projectionMax = Math.max(0, ...projection.map((day) => Number(day.projected_amount)));
  const max = Math.max(historyMax, projectionMax, 1);

  return (
    <div className="finance-chart">
      <div className="finance-chart__bars">
        {history.map((day) => {
          const value = Number(day.total_sales);
          return (
            <div
              key={day.date}
              className="finance-chart__bar"
              style={{ height: `${Math.max((value / max) * 100, value > 0 ? 2 : 0)}%` }}
              title={`${formatShortDate(day.date)}: ${formatCurrency(day.total_sales)} (${day.order_count} órdenes)`}
            />
          );
        })}
        {projection.map((day) => {
          const value = Number(day.projected_amount);
          return (
            <div
              key={day.date}
              className="finance-chart__bar finance-chart__bar--projected"
              style={{ height: `${Math.max((value / max) * 100, value > 0 ? 2 : 0)}%` }}
              title={`${formatShortDate(day.date)} (proyectado): ${formatCurrency(day.projected_amount)}`}
            />
          );
        })}
      </div>
      <div className="finance-chart__legend">
        <span className="finance-chart__legend-item">
          <span className="finance-chart__swatch" /> Ventas reales
        </span>
        <span className="finance-chart__legend-item">
          <span className="finance-chart__swatch finance-chart__swatch--projected" /> Proyección (promedio móvil 7 días)
        </span>
      </div>
    </div>
  );
}

export function FinancialDashboardPage() {
  const { currentTenantId } = useTenantContext();
  const tenantId = currentTenantId as string;
  const [branchId, setBranchId] = useState<string | null>(null);

  const financialQuery = useQuery({
    queryKey: ["financial-dashboard", tenantId, branchId],
    queryFn: () => analyticsApi.financialDashboard(tenantId, branchId),
  });

  return (
    <>
      <PageHeader
        title="Dashboard financiero"
        description="Ventas diarias y flujo de caja proyectado a partir del historial de órdenes."
        action={<BranchSelector tenantId={tenantId} value={branchId} onChange={setBranchId} />}
      />

      <QueryState {...financialQuery} loadingLabel="Calculando flujo de caja…">
        {(report) => (
          <>
            <div className="grid grid--stats">
              <StatTile label={`Ventas (${report.period_days} días)`} value={formatCurrency(report.total_revenue)} />
              <StatTile label="Venta diaria promedio" value={formatCurrency(report.avg_daily_revenue)} />
              <StatTile label="Ticket promedio" value={formatCurrency(report.avg_ticket)} />
              <StatTile
                label="Crecimiento"
                value={
                  report.growth_vs_previous_period === null
                    ? "—"
                    : `${report.growth_vs_previous_period > 0 ? "+" : ""}${report.growth_vs_previous_period.toFixed(1)}%`
                }
                hint={formatGrowth(report.growth_vs_previous_period)}
                danger={(report.growth_vs_previous_period ?? 0) < 0}
              />
            </div>

            <Card
              title="Ventas diarias y proyección"
              subtitle="Los últimos 7 días de la proyección usan el promedio móvil de la venta reciente."
            >
              {report.daily_revenue.length === 0 ? (
                <EmptyState
                  title="Sin ventas registradas"
                  description="Sincroniza órdenes completadas para ver el flujo de caja proyectado."
                />
              ) : (
                <RevenueChart history={report.daily_revenue} projection={report.projection} />
              )}
            </Card>

            <Card title="Proyección de flujo de caja (próximos 7 días)">
              {report.projection.length === 0 ? (
                <EmptyState
                  title="Sin datos suficientes"
                  description="Se necesita al menos un día con ventas registradas para proyectar el flujo de caja."
                />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Fecha</th>
                        <th className="text-right">Monto proyectado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.projection.map((day) => (
                        <tr key={day.date}>
                          <td>{formatLongDate(day.date)}</td>
                          <td className="text-right">{formatCurrency(day.projected_amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </>
        )}
      </QueryState>
    </>
  );
}
