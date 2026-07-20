# Gozsyl — web corporativa

Sitio corporativo de Gozsyl construido con FastAPI, Jinja2 y Tailwind CSS.
Incluye la página principal, información de la empresa y el caso destacado de
Aurexir.

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

La web queda disponible en http://localhost:8000 y puede revisarse sin
configurar servicios adicionales.

Para utilizar otro puerto:

```bash
PORT=8080 npm run dev
```

## Configuración

Copia el archivo de ejemplo cuando quieras personalizar el entorno:

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
| `LOG_LEVEL` | Nivel de registros de la aplicación |

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
| `GET /sitemap.xml` | Sitemap de páginas públicas |
| `GET /robots.txt` | Directivas para buscadores |
| `GET /healthz` | Estado básico de la aplicación |

## Stack

- FastAPI y Uvicorn.
- Jinja2 y JavaScript nativo.
- Tailwind CSS precompilado.

## Producción

El `Dockerfile` instala las dependencias en una imagen multi-stage, ejecuta la
aplicación con Gunicorn y expone el puerto `8000`. Antes de desplegar:

```bash
npm ci
npm run build:css
docker build -t gozsyl-web:latest .
```

Configura las variables de `.env.example` en la plataforma de despliegue y
despliega la imagen generada.
