import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../api/analytics";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
import { QueryState } from "../components/ui/QueryState";
import { RiskPill } from "../components/ui/RiskPill";
import { StatTile } from "../components/ui/StatTile";
import { useTenantContext } from "../context/useTenantContext";
import { formatCurrency, formatNumber } from "../lib/format";

export function StaffAuditPage() {
  const { currentTenantId } = useTenantContext();
  const tenantId = currentTenantId as string;

  const auditQuery = useQuery({
    queryKey: ["staff-audit", tenantId],
    queryFn: () => analyticsApi.staffAudit(tenantId),
  });

  return (
    <>
      <PageHeader
        title="Auditoría de meseros"
        description="Z-Score de cancelaciones y descuentos por mesero, comparado contra el promedio del restaurante."
      />

      <QueryState {...auditQuery} loadingLabel="Analizando cancelaciones…">
        {(report) => (
          <>
            <div className="grid grid--stats">
              <StatTile label="Dinero total en riesgo" value={formatCurrency(report.total_amount_at_risk)} danger={Number(report.total_amount_at_risk) > 0} />
              <StatTile label="Media de cancelaciones" value={formatCurrency(report.restaurant_mean_cancelled)} />
              <StatTile label="Desviación estándar (σ)" value={formatCurrency(report.restaurant_std_cancelled)} />
            </div>

            <Card title="Meseros" subtitle="Ordenados por Z-Score descendente">
              {report.waiters.length === 0 ? (
                <EmptyState
                  title="Sin datos de auditoría"
                  description="Sincroniza órdenes con cancelaciones o descuentos para ver el semáforo por mesero."
                />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Mesero</th>
                        <th className="text-right">Cancelaciones</th>
                        <th className="text-right">Monto cancelado</th>
                        <th className="text-right">Descuentos</th>
                        <th className="text-right">Z-Score</th>
                        <th>Riesgo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.waiters.map((w) => (
                        <tr key={w.staff_id ?? w.staff_name}>
                          <td>{w.staff_name}</td>
                          <td className="text-right">{w.total_cancellations_count}</td>
                          <td className="text-right">{formatCurrency(w.total_cancelled_amount)}</td>
                          <td className="text-right">{formatCurrency(w.total_discount_amount)}</td>
                          <td className="text-right mono">{formatNumber(w.zscore, 2)}</td>
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
          </>
        )}
      </QueryState>
    </>
  );
}
