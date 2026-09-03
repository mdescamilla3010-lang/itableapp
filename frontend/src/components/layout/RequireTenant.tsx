import { Navigate, Outlet } from "react-router-dom";
import { useTenantContext } from "../../context/useTenantContext";

export function RequireTenant() {
  const { currentTenantId } = useTenantContext();

  if (!currentTenantId) {
    return <Navigate to="/tenants" replace />;
  }

  return <Outlet />;
}
