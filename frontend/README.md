# itable app — Frontend

Dashboard de Business Intelligence y Auditoría Operativa para restaurantes. SPA en React +
Vite + TypeScript que consume la API FastAPI del backend (`../app`).

## Stack

- React 19 + TypeScript
- Vite 8 (dev server + build)
- React Router 7 (rutas declarativas)
- TanStack Query 5 (fetching, caché e invalidación tras cada sync)
- CSS plano con variables (sin framework de UI) — ver `src/index.css`

## Estructura

```
src/
├── api/           # Cliente fetch tipado + un módulo por dominio (tenants, sync, analytics, health)
├── components/
│   ├── layout/    # AppShell, Sidebar, TenantSwitcher, HealthIndicator, RequireTenant
│   └── ui/        # Card, StatTile, RiskPill, MenuCategoryPill, QueryState, EmptyState, etc.
├── context/       # TenantContext — tenant actual persistido en localStorage
├── lib/           # format.ts, labels.ts, slugify.ts
├── pages/         # Una página por pantalla del MVP (ver abajo)
└── App.tsx        # Router + providers
```

## Pantallas

| Ruta                 | Página                | Qué muestra |
|-----------------------|------------------------|-------------|
| `/tenants`             | `TenantsPage`          | Alta y selección de tenant (restaurante/cliente) |
| `/`                    | `DashboardPage`        | KPIs ejecutivos: ventas, dinero en riesgo, top meseros/productos |
| `/staff-audit`         | `StaffAuditPage`       | Semáforo de meseros por Z-Score de cancelaciones |
| `/menu-engineering`    | `MenuEngineeringPage`  | Matriz Kasavana & Smith (Estrella/Caballo/Puzzle/Perro) |
| `/cash-audit`          | `CashAuditPage`        | Descuadres de caja acumulados por cajero |
| `/sync-test`           | `SyncTestPage`         | Envía payloads de ejemplo a `/sync` y `/sync/cash-shifts` |

## Autenticación (nota importante)

El backend **no tiene autenticación real** (no hay login ni modelo de usuario, solo
`tenant_id` en la URL). El frontend resuelve la identificación de tenant con un selector simple
persistido en `localStorage` (`TenantContext`) — suficiente para desarrollo/demo interno, pero
**no apto para producción multi-cliente** tal cual. Antes de exponer esto a clientes reales hay
que agregar auth real al backend (JWT o API keys por tenant).

## Levantar el proyecto

```bash
npm install
cp .env.example .env.local   # opcional, los defaults ya apuntan al backend local

npm run dev      # http://localhost:5173 — proxea /api al backend en :8000
npm run build    # tsc -b && vite build -> dist/
npm run preview  # sirve el build de producción localmente
```

El backend debe estar corriendo en `http://localhost:8000` (ver README raíz del repo). El dev
server de Vite proxea `/api/*` hacia él (configurado en `vite.config.ts`), así que en desarrollo
no hace falta configurar CORS ni una URL absoluta.

Para un build de producción apuntando a un backend en otro origen, define `VITE_API_BASE_URL`
en `.env.production` (o al momento del build) con la URL completa del backend, y asegúrate de
que `CORS_ORIGINS` en el backend incluya el origen donde se sirva este frontend.
