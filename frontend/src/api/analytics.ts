import { api } from "./client";
import type {
  CajaAuditReport,
  DashboardSummary,
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
};
