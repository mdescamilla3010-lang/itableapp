import { api } from "./client";
import type {
  AccessCodeRotateResult,
  AccessCodeVerifyResult,
  Branch,
  Tenant,
  TenantCreated,
  TenantCreatePayload,
} from "./types";

export const tenantsApi = {
  list: () => api.get<Tenant[]>("/tenants"),
  get: (tenantId: string) => api.get<Tenant>(`/tenants/${tenantId}`),
  create: (payload: TenantCreatePayload) => api.post<TenantCreated>("/tenants", payload),
  verifyAccess: (tenantId: string, code: string) =>
    api.post<AccessCodeVerifyResult>(`/tenants/${tenantId}/verify-access`, { code }),
  rotateAccessCode: (tenantId: string) =>
    api.post<AccessCodeRotateResult>(`/tenants/${tenantId}/rotate-access-code`, {}),
  branches: (tenantId: string) => api.get<Branch[]>(`/tenants/${tenantId}/branches`),
};
