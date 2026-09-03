import { api } from "./client";
import type { Tenant, TenantCreatePayload } from "./types";

export const tenantsApi = {
  list: () => api.get<Tenant[]>("/tenants"),
  get: (tenantId: string) => api.get<Tenant>(`/tenants/${tenantId}`),
  create: (payload: TenantCreatePayload) => api.post<Tenant>("/tenants", payload),
};
