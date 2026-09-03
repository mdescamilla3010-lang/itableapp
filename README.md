# itable app — Backend MVP

Plataforma SaaS B2B de Business Intelligence y Auditoria Operativa para restaurantes,
conectada vía API a POS externos (ej. Parrot POS).

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL + SQLAlchemy 2.0 (ORM tipado)
- Pydantic v2
- NumPy / Pandas para los motores de analítica

## Arquitectura

```
app/
├── main.py                 # Entrypoint FastAPI, crea las tablas al iniciar
├── core/
│   └── config.py           # Configuración vía variables de entorno (pydantic-settings)
├── db/
│   ├── database.py         # Engine, SessionLocal, Base declarativa, get_db()
│   └── models.py           # Modelos: Tenant, Branch, Staff, Order, OrderItem, CashShift, AuditEvent
├── schemas/                 # Contratos Pydantic v2 (request/response)
│   ├── tenant.py
│   ├── order.py
│   └── analytics.py
├── services/
│   ├── ingestion.py         # ParrotIngestionService — ingesta idempotente de órdenes
│   ├── analytics_fugas.py   # FugasAnalyticsEngine — Z-Score de cancelaciones/descuentos
│   ├── analytics_caja.py    # CajaAnalyticsEngine — descuadres acumulados por cajero
│   └── analytics_menu.py    # MenuEngineeringEngine — matriz Kasavana & Smith
└── api/v1/
    ├── router.py
    └── endpoints/
        ├── health.py
        ├── sync.py
        ├── dashboard.py
        └── analytics.py
```

## Modelo de datos (multi-tenant)

Cada tabla de negocio cuelga de `tenant_id`, aislando los datos de cada restaurante/cliente:

- **Tenant**: cuenta cliente (restaurante/cadena), su API key de Parrot POS y plan de suscripción.
- **Branch**: sucursales del tenant, mapeadas por `external_id` del POS.
- **Staff**: meseros/cajeros, mapeados por `external_id` del POS.
- **Order** / **OrderItem**: órdenes y sus líneas, con costo y precio unitario para calcular margen.
- **CashShift**: turnos de caja con efectivo esperado vs. real (descuadre).
- **AuditEvent**: eventos de auditoría (cancelación, descuento, void), generados automáticamente
  durante la ingesta.

## Motores de inteligencia

### 1. Auditoría de fugas de personal (`FugasAnalyticsEngine`)

Agrupa cancelaciones y descuentos por mesero y calcula el **Z-Score** del monto cancelado
acumulado frente a la media y desviación estándar del restaurante (NumPy):

- `Z-Score >= 2.0` **y** monto cancelado > $1,000 MXN → `HIGH_RISK` 🔴
- `Z-Score >= 1.0` → `MEDIUM_RISK` 🟡
- En otro caso → `NORMAL` 🟢

Devuelve el dinero total en riesgo y el semáforo por mesero.

### 2. Auditoría de caja (`CajaAnalyticsEngine`)

Agrupa los descuadres (`discrepancy`) de `CashShift` por cajero a lo largo del tiempo,
para detectar la acumulación de micro-mermas que individualmente pasarían desapercibidas.

### 3. Ingeniería de menú (`MenuEngineeringEngine`)

Implementa la matriz de **Kasavana & Smith** (popularidad vs. margen de ganancia) y clasifica
cada platillo en:

| Categoría            | Margen | Popularidad | Recomendación                          |
|-----------------------|--------|--------------|-----------------------------------------|
| ESTRELLA              | Alto   | Alta         | Mantener y destacar en el menú          |
| CABALLO_DE_BATALLA    | Bajo   | Alta         | Subir precio o reducir costo de insumo  |
| PUZZLE                | Alto   | Baja         | Promocionar activamente                 |
| PERRO                 | Bajo   | Baja         | Quitar del menú                         |

## Ingesta de datos (`ParrotIngestionService`)

`process_orders_payload` procesa el payload de órdenes de Parrot POS:

1. Previene duplicados verificando `tenant_id` + `external_order_id`.
2. Crea automáticamente `Branch` y `Staff` nuevos si no existen.
3. Si la orden viene `CANCELLED` o con `discount_amount > 0`, crea el `AuditEvent`
   correspondiente (`CANCELLED_ORDER` / `DISCOUNT`) con monto, fecha, razón y mesero.

## Endpoints

| Método | Ruta                                              | Descripción                                   |
|--------|---------------------------------------------------|------------------------------------------------|
| GET    | `/api/v1/health`                                   | Estado de la aplicación                        |
| POST   | `/api/v1/sync/{tenant_id}`                         | Ingesta de órdenes desde Parrot POS             |
| GET    | `/api/v1/dashboard/summary/{tenant_id}`            | KPIs ejecutivos consolidados                    |
| GET    | `/api/v1/analytics/staff-audit/{tenant_id}`        | Auditoría completa de meseros con semáforo      |
| GET    | `/api/v1/analytics/cash-audit/{tenant_id}`         | Descuadres acumulados por cajero                |
| GET    | `/api/v1/analytics/menu-engineering/{tenant_id}`   | Matriz de ingeniería de menú clasificada        |

## Levantar el proyecto

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Ajusta DATABASE_URL a tu instancia de PostgreSQL

uvicorn app.main:app --reload
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.
