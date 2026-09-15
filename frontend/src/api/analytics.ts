import { api } from "./client";
import type {
  CajaAuditReport,
  DashboardSummary,
  FinancialDashboardReport,
  FugasAuditReport,
  MenuEngineeringReport,
} from "./types";

function branchQuery(branchId?: string | null): string {
  return branchId ? `?branch_id=${encodeURIComponent(branchId)}` : "";
}

export const analyticsApi = {
  dashboardSummary: (tenantId: string, branchId?: string | null) =>
    api.get<DashboardSummary>(`/dashboard/summary/${tenantId}${branchQuery(branchId)}`),
  staffAudit: (tenantId: string, branchId?: string | null) =>
    api.get<FugasAuditReport>(`/analytics/staff-audit/${tenantId}${branchQuery(branchId)}`),
  cashAudit: (tenantId: string) =>
    api.get<CajaAuditReport>(`/analytics/cash-audit/${tenantId}`),
  menuEngineering: (tenantId: string, branchId?: string | null) =>
    api.get<MenuEngineeringReport>(`/analytics/menu-engineering/${tenantId}${branchQuery(branchId)}`),
  financialDashboard: (tenantId: string, branchId?: string | null, days = 30) => {
    const params = new URLSearchParams({ days: String(days) });
    if (branchId) params.set("branch_id", branchId);
    return api.get<FinancialDashboardReport>(`/analytics/financial-dashboard/${tenantId}?${params.toString()}`);
  },
};
