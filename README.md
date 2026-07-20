# Gozsyl — web corporativa

Sitio corporativo de Gozsyl construido con FastAPI, Jinja2 y Tailwind CSS.
Incluye la página principal, información de la empresa, el caso destacado de
Aurexir y un blog público de solo lectura.

## Desarrollo local

Requisitos:

- Node.js 18 o superior.
- Python 3.11 o superior. El lanzador detecta automáticamente versiones
  compatibles como `python3.12`.

Desde la raíz del repositorio ejecuta:

```bash
npm run dev
```

El primer arranque:

1. Instala las herramientas de frontend con `npm ci` si hacen falta.
2. Crea `.venv-dev` sin modificar otros entornos virtuales existentes.
3. Instala las dependencias de `requirements.txt`.
4. Inicia FastAPI y Tailwind CSS con recarga automática.

La web queda disponible en http://localhost:8000. Si no existe `.env`, se
activa una vista pública local que no consulta PostgreSQL. Así se puede revisar
el diseño completo sin configurar servicios adicionales.

Para utilizar otro puerto:

```bash
PORT=8080 npm run dev
```

## Configuración

Copia el archivo de ejemplo cuando quieras conectar el blog a PostgreSQL:

```bash
cp .env.example .env
```

Variables disponibles:

| Variable | Descripción |
|---|---|
| `APP_URL` | URL pública y base para canonical, sitemap y Open Graph |
| `APP_NAME` | Nombre visible de la empresa |
| `APP_DESCRIPTION` | Descripción SEO predeterminada |
| `CONTACT_EMAIL` | Correo utilizado por las llamadas a la acción |
| `COMPANY_JURISDICTION` | Jurisdicción mostrada en el sitio |
| `ENVIRONMENT` | `development`, `staging` o `production` |
| `DEV_PREVIEW_MODE` | Omite consultas del blog cuando es `true` |
| `DATABASE_URL` | Conexión `postgresql+asyncpg://...` para el blog |
| `LOG_LEVEL` | Nivel de registros de la aplicación |

Después de configurar PostgreSQL aplica las migraciones:

```bash
.venv-dev/bin/alembic upgrade head
```

## Comandos

```bash
npm run dev        # FastAPI + Tailwind con recarga automática
npm run build:css  # genera la hoja CSS minificada
```

## Rutas públicas

| Ruta | Descripción |
|---|---|
| `GET /` | Página principal |
| `GET /acerca` | Información sobre Gozsyl |
| `GET /blog` | Listado paginado de artículos |
| `GET /blog/{slug}` | Detalle de un artículo publicado |
| `GET /sitemap.xml` | Sitemap dinámico |
| `GET /robots.txt` | Directivas para buscadores |
| `GET /healthz` | Estado básico de la aplicación |

## Stack

- FastAPI y Uvicorn.
- Jinja2 y JavaScript nativo.
- Tailwind CSS precompilado.
- SQLAlchemy async, Alembic y PostgreSQL para el blog.
- Markdown y Bleach para renderizado seguro de artículos.

## Producción

El `Dockerfile` instala las dependencias en una imagen multi-stage, ejecuta la
aplicación con Gunicorn y expone el puerto `8000`. Antes de desplegar:

```bash
npm ci
npm run build:css
docker build -t gozsyl-web:latest .
```

Configura las variables de `.env.example` en la plataforma de despliegue y
ejecuta `alembic upgrade head` cuando utilices el blog conectado a PostgreSQL.
