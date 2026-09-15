import { useCallback, useMemo, useState, type ReactNode } from "react";
import { setAccessToken } from "../lib/session";
import { TenantContext } from "./tenantContextStore";

const STORAGE_KEY = "itable:currentTenantId";

export function TenantProvider({ children }: { children: ReactNode }) {
  const [currentTenantId, setCurrentTenantId] = useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  });

  const selectTenant = useCallback((tenantId: string, accessToken: string) => {
    try {
      localStorage.setItem(STORAGE_KEY, tenantId);
    } catch {
      // localStorage unavailable (private mode, etc.) — state still works in-memory
    }
    setAccessToken(accessToken);
    setCurrentTenantId(tenantId);
  }, []);

  const clearTenant = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setAccessToken(null);
    setCurrentTenantId(null);
  }, []);

  const value = useMemo(
    () => ({ currentTenantId, selectTenant, clearTenant }),
    [currentTenantId, selectTenant, clearTenant],
  );

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}
