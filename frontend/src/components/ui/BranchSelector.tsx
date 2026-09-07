import { useQuery } from "@tanstack/react-query";
import { tenantsApi } from "../../api/tenants";

interface BranchSelectorProps {
  tenantId: string;
  value: string | null;
  onChange: (branchId: string | null) => void;
}

export function BranchSelector({ tenantId, value, onChange }: BranchSelectorProps) {
  const branchesQuery = useQuery({
    queryKey: ["branches", tenantId],
    queryFn: () => tenantsApi.branches(tenantId),
  });

  const branches = branchesQuery.data ?? [];
  if (branches.length <= 1) return null;

  return (
    <div className="field" style={{ maxWidth: "260px" }}>
      <label htmlFor="branch-selector">Sucursal</label>
      <select
        id="branch-selector"
        className="input"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
      >
        <option value="">Todas las sucursales</option>
        {branches.map((branch) => (
          <option key={branch.id} value={branch.id}>
            {branch.name}
          </option>
        ))}
      </select>
    </div>
  );
}
