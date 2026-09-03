import { useQuery } from "@tanstack/react-query";
import { healthApi } from "../../api/health";

export function HealthIndicator() {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    refetchInterval: 30_000,
    retry: false,
  });

  const online = Boolean(data) && !isError;

  return (
    <span className="tenant-switcher" title={online ? "Backend conectado" : "Backend no responde"}>
      <span className={`status-dot ${online ? "status-dot--online" : "status-dot--offline"}`} />
      <span>{online ? "API en línea" : "API sin conexión"}</span>
    </span>
  );
}
