import { api } from "./client";
import type {
  CajaAuditReport,
  DashboardSummary,
  FugasAuditReport,
  MenuEngineeringReport,
} from "./types";

export const analyticsApi = {
  dashboardSummary: (tenantId: string) =>
    api.get<DashboardSummary>(`/dashboard/summary/${tenantId}`),
  staffAudit: (tenantId: string) =>
    api.get<FugasAuditReport>(`/analytics/staff-audit/${tenantId}`),
  cashAudit: (tenantId: string) =>
    api.get<CajaAuditReport>(`/analytics/cash-audit/${tenantId}`),
  menuEngineering: (tenantId: string) =>
    api.get<MenuEngineeringReport>(`/analytics/menu-engineering/${tenantId}`),
};
