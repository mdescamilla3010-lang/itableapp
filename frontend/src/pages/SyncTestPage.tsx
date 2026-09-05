import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { syncApi } from "../api/sync";
import { ApiError } from "../api/client";
import { Card } from "../components/ui/Card";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { PageHeader } from "../components/ui/PageHeader";
import { useTenantContext } from "../context/useTenantContext";

const ORDERS_TEMPLATE_CSV = `external_order_id,external_product_id,product_name,category_name,quantity,unit_price,unit_cost,order_date,staff_external_id,staff_name,branch_external_id,branch_name,table_name,status,discount_amount,discount_reason,payment_method,total_amount
ORD-1001,P-TACOS,Tacos al Pastor,Comida,6,70.00,25.00,2024-05-01 13:00,W-1,Juan Perez,BR-1,Sucursal Centro,Mesa 5,COMPLETED,0,,cash,
ORD-1002,P-PIZZA,Pizza Especial,Comida,2,490.00,180.00,2024-05-01 14:00,W-2,Maria Lopez,BR-1,Sucursal Centro,Mesa 3,CANCELLED,0,,card,
`;

const CASH_SHIFTS_TEMPLATE_CSV = `external_shift_id,staff_external_id,staff_name,expected_cash,actual_cash,shift_start,shift_end
SH-1001,W-1,Juan Perez,1200.00,1150.00,2024-05-01 12:00,2024-05-01 20:00
`;

function downloadTextFile(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

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
        title="Ingesta de datos"
        description="Carga datos de demo, sube un CSV/Excel de cualquier POS, o prueba el payload JSON estilo Parrot POS directamente."
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
        <>
          <FileUploadCard
            key="orders-upload"
            title="Subir archivo de ventas (cualquier POS)"
            description="Exporta tus ventas desde tu POS a CSV o Excel y súbelas aquí. No necesitas una integración a la medida."
            requiredColumns="external_order_id, external_product_id, product_name, order_date"
            templateFilename="plantilla_ventas.csv"
            templateContent={ORDERS_TEMPLATE_CSV}
            upload={(file) => syncApi.uploadOrdersFile(tenantId, file)}
            renderSuccess={(data) =>
              `Listo: ${data.orders_created} órdenes creadas, ${data.orders_skipped_duplicate} duplicadas, ${data.rows_skipped_invalid} filas inválidas omitidas.`
            }
          />
          <SyncPanel
            key="orders"
            title="POST /sync/{tenant_id}"
            description="Crea órdenes nuevas, registra sucursales/meseros automáticamente y genera AuditEvents por cancelaciones o descuentos."
            defaultPayload={EXAMPLE_ORDERS_PAYLOAD}
            submit={(payload) => syncApi.orders(tenantId, payload as never)}
          />
        </>
      ) : (
        <>
          <FileUploadCard
            key="cash-shifts-upload"
            title="Subir archivo de cortes de caja (cualquier POS)"
            description="Exporta tus cortes de caja desde tu POS a CSV o Excel y súbelos aquí."
            requiredColumns="external_shift_id, expected_cash, actual_cash, shift_start"
            templateFilename="plantilla_cortes_caja.csv"
            templateContent={CASH_SHIFTS_TEMPLATE_CSV}
            upload={(file) => syncApi.uploadCashShiftsFile(tenantId, file)}
            renderSuccess={(data) =>
              `Listo: ${data.shifts_created} cortes creados, ${data.shifts_skipped_duplicate} duplicados, ${data.rows_skipped_invalid} filas inválidas omitidas.`
            }
          />
          <SyncPanel
            key="cash-shifts"
            title="POST /sync/{tenant_id}/cash-shifts"
            description="Crea cortes de caja, registra cajeros automáticamente y calcula el descuadre (actual - esperado)."
            defaultPayload={EXAMPLE_CASH_SHIFTS_PAYLOAD}
            submit={(payload) => syncApi.cashShifts(tenantId, payload as never)}
          />
        </>
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

interface FileUploadCardProps<T> {
  title: string;
  description: string;
  requiredColumns: string;
  templateFilename: string;
  templateContent: string;
  upload: (file: File) => Promise<T>;
  renderSuccess: (data: T) => string;
}

function FileUploadCard<T>({
  title,
  description,
  requiredColumns,
  templateFilename,
  templateContent,
  upload,
  renderSuccess,
}: FileUploadCardProps<T>) {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["staff-audit"] });
      queryClient.invalidateQueries({ queryKey: ["menu-engineering"] });
      queryClient.invalidateQueries({ queryKey: ["cash-audit"] });
    },
  });

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    mutation.reset();
    mutation.mutate(file);
    event.target.value = "";
  }

  return (
    <Card title={title} subtitle={description}>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <p className="text-muted" style={{ margin: 0 }}>
          Columnas requeridas: <code className="mono">{requiredColumns}</code>
        </p>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => inputRef.current?.click()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "Subiendo…" : "Elegir archivo (.csv, .xlsx)"}
          </button>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => downloadTextFile(templateFilename, templateContent)}
          >
            Descargar plantilla
          </button>
          {fileName && <span className="text-muted">{fileName}</span>}
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
        </div>

        {mutation.isError && <ErrorBanner error={mutation.error} />}
        {mutation.isSuccess && (
          <div className="banner banner--success">
            <span>✓</span>
            <span>{renderSuccess(mutation.data)}</span>
          </div>
        )}
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
