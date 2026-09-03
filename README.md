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
├── main.py                 # Entrypoint FastAPI (el esquema lo gestiona Alembic, no la app)
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
        ├── tenants.py
        ├── sync.py
        ├── dashboard.py
        └── analytics.py

alembic/
├── env.py                   # Usa app.core.config.settings.DATABASE_URL y Base.metadata
└── versions/
    └── d1d0b376db08_initial_schema.py
alembic.ini
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
| POST   | `/api/v1/tenants`                                  | Alta de un nuevo tenant (restaurante/cliente)   |
| GET    | `/api/v1/tenants/{tenant_id}`                      | Detalle de un tenant                            |
| POST   | `/api/v1/sync/{tenant_id}`                         | Ingesta de órdenes desde Parrot POS             |
| GET    | `/api/v1/dashboard/summary/{tenant_id}`            | KPIs ejecutivos consolidados                    |
| GET    | `/api/v1/analytics/staff-audit/{tenant_id}`        | Auditoría completa de meseros con semáforo      |
| GET    | `/api/v1/analytics/cash-audit/{tenant_id}`         | Descuadres acumulados por cajero                |
| GET    | `/api/v1/analytics/menu-engineering/{tenant_id}`   | Matriz de ingeniería de menú clasificada        |

`POST /api/v1/tenants` devuelve `409 Conflict` si el `slug` ya existe (debe ser único por tenant).

## Migraciones (Alembic)

El esquema de base de datos se gestiona exclusivamente con **Alembic** — la app ya no crea
tablas automáticamente al arrancar (`Base.metadata.create_all` fue removido de `main.py`).
`alembic/env.py` lee `DATABASE_URL` directamente de `app.core.config.settings`, así que basta
con tener el `.env` configurado.

```bash
# Aplicar todas las migraciones pendientes (requerido antes de levantar la app)
alembic upgrade head

# Generar una nueva migración tras modificar app/db/models.py
alembic revision --autogenerate -m "descripcion del cambio"

# Revertir la última migración
alembic downgrade -1
```

La migración inicial (`alembic/versions/d1d0b376db08_initial_schema.py`) crea las 7 tablas
del modelo de datos con sus índices y foreign keys (`CASCADE` / `SET NULL` según corresponda).

## Tests

Los tests (`tests/`) corren contra una base PostgreSQL real (no SQLite/mocks), previamente
migrada con Alembic. Cada test parte de una base limpia gracias a un fixture `autouse` en
`tests/conftest.py` que borra los `Tenant` al finalizar (cascada al resto de las tablas).

```bash
pip install -r requirements-dev.txt

# Contra una base de pruebas dedicada
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/itable_test
alembic upgrade head
pytest -v
```

Cobertura actual: ingesta (`test_ingestion.py`), motor de fugas/Z-Score (`test_analytics_fugas.py`),
auditoría de caja (`test_analytics_caja.py`), ingeniería de menú (`test_analytics_menu.py`) y los
endpoints REST end-to-end (`test_api.py`).

## CI (GitHub Actions)

`.github/workflows/ci.yml` corre en cada push/PR a `main`:

1. Levanta un servicio `postgres:16` (con health check) como base de datos del job.
2. Instala `requirements-dev.txt`.
3. Aplica el esquema con `alembic upgrade head`.
4. Corre `pytest -v`.

Así el pipeline valida en cada cambio que las migraciones se apliquen limpio sobre una base
nueva y que la suite de tests pase contra ese esquema real.

## Levantar el proyecto

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Ajusta DATABASE_URL a tu instancia de PostgreSQL

alembic upgrade head
uvicorn app.main:app --reload
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.
