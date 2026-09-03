import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../api/analytics";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";
import { QueryState } from "../components/ui/QueryState";
import { StatTile } from "../components/ui/StatTile";
import { useTenantContext } from "../context/TenantContext";
import { formatCurrency } from "../lib/format";

export function CashAuditPage() {
  const { currentTenantId } = useTenantContext();
  const tenantId = currentTenantId as string;

  const cashQuery = useQuery({
    queryKey: ["cash-audit", tenantId],
    queryFn: () => analyticsApi.cashAudit(tenantId),
  });

  return (
    <>
      <PageHeader
        title="Auditoría de caja"
        description="Descuadres acumulados por cajero a lo largo del tiempo — detecta micro-mermas sostenidas, no solo incidentes aislados."
      />

      <QueryState {...cashQuery} loadingLabel="Sumando descuadres…">
        {(report) => (
          <>
            <div className="grid grid--stats">
              <StatTile
                label="Descuadre total acumulado"
                value={formatCurrency(report.total_accumulated_discrepancy)}
                danger={Number(report.total_accumulated_discrepancy) < 0}
              />
            </div>

            <Card title="Cajeros" subtitle="Ordenados por descuadre acumulado (mayor riesgo primero)">
              {report.cashiers.length === 0 ? (
                <EmptyState
                  title="Sin turnos de caja registrados"
                  description="Sincroniza cortes de caja para ver descuadres por cajero."
                />
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Cajero</th>
                        <th className="text-right">Turnos</th>
                        <th className="text-right">Efectivo esperado</th>
                        <th className="text-right">Efectivo real</th>
                        <th className="text-right">Descuadre acumulado</th>
                        <th className="text-right">Promedio por turno</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.cashiers.map((c) => (
                        <tr key={c.staff_id ?? c.staff_name}>
                          <td>{c.staff_name}</td>
                          <td className="text-right">{c.shifts_count}</td>
                          <td className="text-right">{formatCurrency(c.total_expected_cash)}</td>
                          <td className="text-right">{formatCurrency(c.total_actual_cash)}</td>
                          <td className={`text-right ${Number(c.accumulated_discrepancy) < 0 ? "stat-tile__value--danger" : ""}`}>
                            {formatCurrency(c.accumulated_discrepancy)}
                          </td>
                          <td className="text-right text-muted">{formatCurrency(c.average_discrepancy)}</td>
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
