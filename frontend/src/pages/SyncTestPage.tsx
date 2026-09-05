import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { syncApi } from "../api/sync";
import { ApiError } from "../api/client";
import { Card } from "../components/ui/Card";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { PageHeader } from "../components/ui/PageHeader";
import { useTenantContext } from "../context/useTenantContext";

const EXAMPLE_ORDERS_PAYLOAD = {
  orders: [
    {
      external_order_id: "ORD-1001",
      branch_external_id: "BR-1",
      branch_name: "Sucursal Centro",
      staff_external_id: "W-1",
      staff_name: "Juan Perez",
      table_name: "Mesa 5",
      total_amount: "540.00",
      discount_amount: "0",
      payment_method: "cash",
      status: "COMPLETED",
      order_date: new Date().toISOString(),
      items: [
        {
          external_product_id: "P-TACOS",
          product_name: "Tacos al Pastor",
          category_name: "Comida",
          quantity: 6,
          unit_price: "70.00",
          unit_cost: "25.00",
        },
      ],
    },
    {
      external_order_id: "ORD-1002",
      branch_external_id: "BR-1",
      branch_name: "Sucursal Centro",
      staff_external_id: "W-2",
      staff_name: "Maria Lopez",
      table_name: "Mesa 3",
      total_amount: "980.00",
      discount_amount: "0",
      payment_method: "card",
      status: "CANCELLED",
      order_date: new Date().toISOString(),
      items: [
        {
          external_product_id: "P-PIZZA",
          product_name: "Pizza Especial",
          category_name: "Comida",
          quantity: 2,
          unit_price: "490.00",
          unit_cost: "180.00",
        },
      ],
    },
  ],
};

const EXAMPLE_CASH_SHIFTS_PAYLOAD = {
  shifts: [
    {
      external_shift_id: "SH-1001",
      staff_external_id: "W-1",
      staff_name: "Juan Perez",
      expected_cash: "1200.00",
      actual_cash: "1150.00",
      shift_start: new Date().toISOString(),
    },
  ],
};

type Tab = "orders" | "cash-shifts";

export function SyncTestPage() {
  const { currentTenantId } = useTenantContext();
  const tenantId = currentTenantId as string;
  const [tab, setTab] = useState<Tab>("orders");

  return (
    <>
      <PageHeader
        title="Probar ingesta"
        description="Envía un payload de ejemplo (estilo Parrot POS) al tenant seleccionado para ver la ingesta funcionando en vivo."
      />

      <DemoDataCard tenantId={tenantId} />

      <div className="tabs">
        <button className={`tab${tab === "orders" ? " active" : ""}`} onClick={() => setTab("orders")}>
          Órdenes
        </button>
        <button
          className={`tab${tab === "cash-shifts" ? " active" : ""}`}
          onClick={() => setTab("cash-shifts")}
        >
          Cortes de caja
        </button>
      </div>

      {tab === "orders" ? (
        <SyncPanel
          key="orders"
          title="POST /sync/{tenant_id}"
          description="Crea órdenes nuevas, registra sucursales/meseros automáticamente y genera AuditEvents por cancelaciones o descuentos."
          defaultPayload={EXAMPLE_ORDERS_PAYLOAD}
          submit={(payload) => syncApi.orders(tenantId, payload as never)}
        />
      ) : (
        <SyncPanel
          key="cash-shifts"
          title="POST /sync/{tenant_id}/cash-shifts"
          description="Crea cortes de caja, registra cajeros automáticamente y calcula el descuadre (actual - esperado)."
          defaultPayload={EXAMPLE_CASH_SHIFTS_PAYLOAD}
          submit={(payload) => syncApi.cashShifts(tenantId, payload as never)}
        />
      )}
    </>
  );
}

function DemoDataCard({ tenantId }: { tenantId: string }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => syncApi.seedDemoData(tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["staff-audit"] });
      queryClient.invalidateQueries({ queryKey: ["menu-engineering"] });
      queryClient.invalidateQueries({ queryKey: ["cash-audit"] });
    },
  });

  return (
    <Card
      title="Generar datos de demostración"
      subtitle="Crea ~3 semanas de ventas, meseros y cortes de caja de ejemplo para este tenant, con un clic — sin necesidad de terminal ni de un POS real conectado."
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {mutation.isError && <ErrorBanner error={mutation.error} />}
        {mutation.isSuccess && (
          <div className="banner banner--success">
            <span>✓</span>
            <span>
              Listo: {mutation.data.orders.orders_created} órdenes y{" "}
              {mutation.data.cash_shifts.shifts_created} cortes de caja creados. Revisa el Dashboard.
            </span>
          </div>
        )}
        <div>
          <button
            className="btn btn--primary"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Generando…" : "Generar datos de demo"}
          </button>
        </div>
      </div>
    </Card>
  );
}

interface SyncPanelProps {
  title: string;
  description: string;
  defaultPayload: object;
  submit: (payload: unknown) => Promise<unknown>;
}

function SyncPanel({ title, description, defaultPayload, submit }: SyncPanelProps) {
  const queryClient = useQueryClient();
  const [text, setText] = useState(() => JSON.stringify(defaultPayload, null, 2));
  const [parseError, setParseError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: submit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["staff-audit"] });
      queryClient.invalidateQueries({ queryKey: ["menu-engineering"] });
      queryClient.invalidateQueries({ queryKey: ["cash-audit"] });
    },
  });

  function handleSubmit() {
    setParseError(null);
    mutation.reset();
    let payload: unknown;
    try {
      payload = JSON.parse(text);
    } catch {
      setParseError("El JSON no es válido. Revisa la sintaxis.");
      return;
    }
    mutation.mutate(payload);
  }

  return (
    <Card title={title} subtitle={description}>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <div className="field">
          <label>Payload JSON</label>
          <textarea className="input" value={text} onChange={(e) => setText(e.target.value)} spellCheck={false} />
        </div>

        {parseError && <ErrorBanner error={new ApiError(0, parseError)} />}
        {mutation.isError && <ErrorBanner error={mutation.error} />}
        {mutation.isSuccess && (
          <div className="banner banner--success">
            <span>✓</span>
            <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
              {JSON.stringify(mutation.data, null, 2)}
            </pre>
          </div>
        )}

        <div>
          <button className="btn btn--primary" onClick={handleSubmit} disabled={mutation.isPending}>
            {mutation.isPending ? "Enviando…" : "Enviar payload"}
          </button>
        </div>
      </div>
    </Card>
  );
}
