import { useContext } from "react";
import { TenantContext, type TenantContextValue } from "./tenantContextStore";

export function useTenantContext(): TenantContextValue {
  const ctx = useContext(TenantContext);
  if (!ctx) {
    throw new Error("useTenantContext must be used within a TenantProvider");
  }
  return ctx;
}
