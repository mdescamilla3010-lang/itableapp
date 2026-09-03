import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { tenantsApi } from "../api/tenants";
import { ApiError } from "../api/client";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { PageHeader } from "../components/ui/PageHeader";
import { LoadingRow } from "../components/ui/Spinner";
import { useTenantContext } from "../context/useTenantContext";
import { formatDate } from "../lib/format";
import { slugify } from "../lib/slugify";

export function TenantsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { currentTenantId, selectTenant } = useTenantContext();

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugTouched, setSlugTouched] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const tenantsQuery = useQuery({ queryKey: ["tenants"], queryFn: tenantsApi.list });

  const createMutation = useMutation({
    mutationFn: tenantsApi.create,
    onSuccess: (tenant) => {
      queryClient.invalidateQueries({ queryKey: ["tenants"] });
      setName("");
      setSlug("");
      setSlugTouched(false);
      setFormError(null);
      selectTenant(tenant.id);
      navigate("/");
    },
    onError: (error: unknown) => {
      setFormError(error instanceof ApiError ? error.message : "No se pudo crear el tenant.");
    },
  });

  function handleNameChange(value: string) {
    setName(value);
    if (!slugTouched) setSlug(slugify(value));
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim() || !slug.trim()) return;
    createMutation.mutate({ name: name.trim(), slug: slug.trim() });
  }

  return (
    <>
      <PageHeader
        title="Tenants"
        description="Cada tenant representa un restaurante o cadena cliente. Selecciona uno para trabajar con él en el resto de la app."
      />

      <Card title="Nuevo tenant">
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="grid grid--two">
            <div className="field">
              <label htmlFor="tenant-name">Nombre</label>
              <input
                id="tenant-name"
                className="input"
                placeholder="Restaurante Demo"
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="tenant-slug">Slug (identificador único)</label>
              <input
                id="tenant-slug"
                className="input mono"
                placeholder="restaurante-demo"
                value={slug}
                onChange={(e) => {
                  setSlugTouched(true);
                  setSlug(e.target.value);
                }}
                required
              />
            </div>
          </div>
          {formError && <ErrorBanner error={new ApiError(0, formError)} />}
          <div>
            <button type="submit" className="btn btn--primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creando…" : "Crear tenant"}
            </button>
          </div>
        </form>
      </Card>

      <Card title="Tenants existentes" subtitle="Haz clic en un tenant para seleccionarlo.">
        {tenantsQuery.isLoading && <LoadingRow />}
        {tenantsQuery.error && <ErrorBanner error={tenantsQuery.error} />}
        {tenantsQuery.data && tenantsQuery.data.length === 0 && (
          <EmptyState
            title="Todavía no hay tenants"
            description="Crea el primero con el formulario de arriba."
          />
        )}
        {tenantsQuery.data && tenantsQuery.data.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Slug</th>
                  <th>Plan</th>
                  <th>Estado</th>
                  <th>Creado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {tenantsQuery.data.map((tenant) => (
                  <tr
                    key={tenant.id}
                    onClick={() => {
                      selectTenant(tenant.id);
                      navigate("/");
                    }}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      {tenant.name}
                      {tenant.id === currentTenantId && (
                        <span className="pill pill--primary" style={{ marginLeft: "8px" }}>
                          Activo
                        </span>
                      )}
                    </td>
                    <td className="mono text-muted">{tenant.slug}</td>
                    <td>{tenant.subscription_plan}</td>
                    <td>
                      <span className={`pill ${tenant.is_active ? "pill--success" : "pill--neutral"}`}>
                        {tenant.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className="text-muted">{formatDate(tenant.created_at)}</td>
                    <td className="text-right">
                      <button
                        type="button"
                        className="btn btn--secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          selectTenant(tenant.id);
                          navigate("/");
                        }}
                      >
                        Seleccionar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
