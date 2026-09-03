import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { tenantsApi } from "../../api/tenants";
import { useTenantContext } from "../../context/TenantContext";
import { ChevronDownIcon } from "./icons";

export function TenantSwitcher() {
  const { currentTenantId } = useTenantContext();

  const { data: tenant, isLoading } = useQuery({
    queryKey: ["tenant", currentTenantId],
    queryFn: () => tenantsApi.get(currentTenantId as string),
    enabled: Boolean(currentTenantId),
    retry: false,
  });

  if (!currentTenantId) {
    return (
      <Link to="/tenants" className="btn btn--secondary">
        Elegir tenant
      </Link>
    );
  }

  return (
    <Link to="/tenants" className="tenant-switcher" title="Cambiar de tenant">
      <span className="tenant-switcher__name">
        {isLoading ? "Cargando…" : tenant?.name ?? "Tenant no encontrado"}
      </span>
      <ChevronDownIcon width={14} height={14} className="text-subtle" />
    </Link>
  );
}
