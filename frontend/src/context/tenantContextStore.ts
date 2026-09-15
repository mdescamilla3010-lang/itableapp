import { createContext } from "react";

export interface TenantContextValue {
  currentTenantId: string | null;
  selectTenant: (tenantId: string, accessToken: string) => void;
  clearTenant: () => void;
}

export const TenantContext = createContext<TenantContextValue | undefined>(undefined);
