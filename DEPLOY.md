# Deploy a Railway (backend + Postgres + frontend)

Esta guía asume que ya tienes el código en GitHub (`mdescamilla3010-lang/itableapp`,
rama `main`) y una cuenta en [railway.app](https://railway.app) (puedes crearla con tu
cuenta de GitHub, tiene un plan de prueba gratuito y luego es de pago por uso).

El repo ya está preparado para esto:
- `Procfile` (raíz) — arranca el backend: `alembic upgrade head && uvicorn ...`
- `frontend/Procfile` — arranca el frontend: sirve el build estático con `serve`
- `app/core/config.py` normaliza automáticamente el `DATABASE_URL` que te da el
  addon de Postgres de Railway (viene como `postgres://...`, SQLAlchemy necesita
  `postgresql+psycopg2://...`)

Vas a crear **3 cosas dentro de un mismo proyecto de Railway**: una base de datos
Postgres, un servicio para el backend, y un servicio para el frontend.

## 1. Crear el proyecto y la base de datos

1. En Railway: **New Project** → **Deploy from GitHub repo** → selecciona
   `mdescamilla3010-lang/itableapp`.
2. Railway crea un primer servicio apuntando a la raíz del repo — esto va a ser tu
   **backend** (déjalo, lo configuras en el paso 2).
3. Dentro del mismo proyecto: **+ New** → **Database** → **Add PostgreSQL**.

## 2. Configurar el servicio de backend

En el servicio creado en el paso 1 (renómbralo a "backend" si quieres, desde
Settings → nombre):

1. **Settings → Source**: Root Directory debe quedar en `/` (la raíz, es el
   default — no la cambies para este servicio).
2. **Variables**: agrega estas dos variables:
   - `DATABASE_URL` → click en el botón de referencia y elige la variable
     `DATABASE_URL` del servicio de Postgres que creaste (Railway te la sugiere
     automáticamente; queda como `${{Postgres.DATABASE_URL}}`).
   - `CORS_ORIGINS` → por ahora déjalo en `*` (lo vas a corregir en el paso 4,
     una vez que tengas la URL del frontend).
3. **Settings → Networking**: click **Generate Domain**. Copia esa URL — algo
   como `https://itableapp-backend-production.up.railway.app`. La vas a necesitar
   en el paso 3.
4. Railway ya debería estar construyendo y desplegando (usa `Procfile`, que corre
   `alembic upgrade head` antes de levantar `uvicorn`). Revisa los logs del
   deploy hasta que diga que está corriendo, y prueba
   `https://<tu-url-de-backend>/api/v1/health` en el navegador — debe responder
   `{"status":"ok",...}`.

## 3. Configurar el servicio de frontend

1. Dentro del mismo proyecto: **+ New** → **GitHub Repo** → el mismo repo otra
   vez. Esto crea un segundo servicio.
2. **Settings → Source**: cambia Root Directory a `frontend`.
3. **Variables**: agrega:
   - `VITE_API_BASE_URL` → la URL del backend que copiaste en el paso 2.3 (sin
     `/` al final), ej. `https://itableapp-backend-production.up.railway.app`.
4. **Settings → Networking**: click **Generate Domain**. Esta es la URL final
   que vas a compartir/abrir en tu navegador — algo como
   `https://itableapp-frontend-production.up.railway.app`.
5. Railway construye con `npm ci && npm run build` y arranca con
   `frontend/Procfile` (`npm run start`, que sirve `dist/` con `serve`).

## 4. Cerrar el círculo: restringir CORS

Ahora que tienes la URL real del frontend (paso 3.4):

1. Vuelve al servicio de **backend** → **Variables**.
2. Cambia `CORS_ORIGINS` de `*` a la URL del frontend, ej.
   `https://itableapp-frontend-production.up.railway.app` (sin `/` al final).
3. Esto dispara un redeploy automático del backend con la config correcta.

## 5. Listo

Abre la URL del frontend (paso 3.4) en tu navegador — esa es tu app real, con URL
pública, corriendo 24/7 (mientras el proyecto de Railway esté activo).

## Notas importantes

- **No hay autenticación real todavía** (ver `frontend/README.md`, sección
  "Autenticación"). Cualquiera con la URL puede crear/editar datos de cualquier
  tenant. Bien para probar internamente; antes de compartirlo con clientes reales
  hay que agregar login/API keys al backend.
- Cada push a `main` en GitHub dispara un redeploy automático en ambos servicios
  (Railway está conectado al repo).
- Si cambias variables de entorno del frontend (`VITE_API_BASE_URL`), Railway
  tiene que **reconstruir** el servicio (no solo reiniciarlo), porque Vite
  incrusta esas variables en el build — Railway hace esto automático al guardar
  la variable.
