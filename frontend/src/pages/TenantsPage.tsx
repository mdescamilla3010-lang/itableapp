import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { tenantsApi } from "../api/tenants";
import { ApiError } from "../api/client";
import type { Tenant } from "../api/types";
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
  const [revealedCode, setRevealedCode] = useState<{ tenantName: string; code: string; isNew: boolean } | null>(
    null,
  );
  const [pendingTenant, setPendingTenant] = useState<Tenant | null>(null);

  function handleChooseTenant(tenant: Tenant) {
    if (tenant.code_required) {
      setPendingTenant(tenant);
    } else {
      selectTenant(tenant.id);
      navigate("/");
    }
  }

  const tenantsQuery = useQuery({ queryKey: ["tenants"], queryFn: tenantsApi.list });

  const createMutation = useMutation({
    mutationFn: tenantsApi.create,
    onSuccess: (tenant) => {
      queryClient.invalidateQueries({ queryKey: ["tenants"] });
      setName("");
      setSlug("");
      setSlugTouched(false);
      setFormError(null);
      setRevealedCode({ tenantName: tenant.name, code: tenant.access_code, isNew: true });
    },
    onError: (error: unknown) => {
      setFormError(error instanceof ApiError ? error.message : "No se pudo crear el tenant.");
    },
  });

  const rotateMutation = useMutation({
    mutationFn: (tenant: Tenant) => tenantsApi.rotateAccessCode(tenant.id),
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

  function handleRotateCode(tenant: Tenant) {
    rotateMutation.mutate(tenant, {
      onSuccess: (result) => {
        setRevealedCode({ tenantName: tenant.name, code: result.access_code, isNew: false });
      },
    });
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
                  <th>Acceso</th>
                  <th>Creado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {tenantsQuery.data.map((tenant) => (
                  <tr key={tenant.id} onClick={() => handleChooseTenant(tenant)} style={{ cursor: "pointer" }}>
                    <td>
                      {tenant.name}
                      {tenant.id === currentTenantId && (
                        <span className="pill pill--primary" style={{ marginLeft: "8px" }}>
                          <span className="pill__dot" />
                          Activo
                        </span>
                      )}
                    </td>
                    <td className="mono text-muted">{tenant.slug}</td>
                    <td>{tenant.subscription_plan}</td>
                    <td>
                      <span className={`pill ${tenant.is_active ? "pill--success" : "pill--neutral"}`}>
                        <span className="pill__dot" />
                        {tenant.is_active ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td>
                      <span className={`pill ${tenant.code_required ? "pill--success" : "pill--warning"}`}>
                        <span className="pill__dot" />
                        {tenant.code_required ? "Protegido" : "Sin código"}
                      </span>
                    </td>
                    <td className="text-muted">{formatDate(tenant.created_at)}</td>
                    <td className="text-right" style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
                      <button
                        type="button"
                        className="btn btn--secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRotateCode(tenant);
                        }}
                        disabled={rotateMutation.isPending}
                      >
                        Generar código
                      </button>
                      <button
                        type="button"
                        className="btn btn--secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleChooseTenant(tenant);
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

      {pendingTenant && (
        <AccessCodePrompt
          tenant={pendingTenant}
          onCancel={() => setPendingTenant(null)}
          onSuccess={() => {
            selectTenant(pendingTenant.id);
            setPendingTenant(null);
            navigate("/");
          }}
        />
      )}

      {revealedCode && (
        <div className="modal-overlay" onClick={() => setRevealedCode(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: 0 }}>
              {revealedCode.isNew ? "Tenant creado" : "Nuevo código de acceso"}
            </h3>
            <p className="text-muted" style={{ margin: 0 }}>
              Este es el código de acceso de <strong>{revealedCode.tenantName}</strong>.
              Compártelo con tu cliente — no se vuelve a mostrar después de cerrar esta ventana.
            </p>
            <div className="access-code-display">{revealedCode.code}</div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                className="btn btn--secondary"
                onClick={() => navigator.clipboard?.writeText(revealedCode.code)}
              >
                Copiar código
              </button>
              <button type="button" className="btn btn--primary" onClick={() => setRevealedCode(null)}>
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function AccessCodePrompt({
  tenant,
  onCancel,
  onSuccess,
}: {
  tenant: Tenant;
  onCancel: () => void;
  onSuccess: () => void;
}) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  const verifyMutation = useMutation({
    mutationFn: () => tenantsApi.verifyAccess(tenant.id, code.trim()),
    onSuccess: (result) => {
      if (result.valid) {
        onSuccess();
      } else {
        setError("Código incorrecto. Verifica con quien te lo compartió.");
      }
    },
    onError: () => setError("No se pudo verificar el código. Intenta de nuevo."),
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (!code.trim()) return;
    verifyMutation.mutate();
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 style={{ margin: 0 }}>Código de acceso</h3>
        <p className="text-muted" style={{ margin: 0 }}>
          Ingresa el código de acceso de <strong>{tenant.name}</strong> para ver su información.
        </p>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <input
            className="input mono"
            style={{ textAlign: "center", fontSize: "20px", letterSpacing: "0.1em" }}
            placeholder="000000"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            autoFocus
            maxLength={12}
          />
          {error && <ErrorBanner error={new ApiError(0, error)} />}
          <div style={{ display: "flex", gap: "8px" }}>
            <button type="button" className="btn btn--secondary" onClick={onCancel} style={{ flex: 1 }}>
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn--primary"
              style={{ flex: 1 }}
              disabled={verifyMutation.isPending}
            >
              {verifyMutation.isPending ? "Verificando…" : "Continuar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
