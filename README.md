# Gozsyl — web corporativa

Sitio corporativo bilingüe de Gozsyl construido con FastAPI, Jinja2 y Tailwind
CSS. Incluye la página principal, información de la empresa, un formulario de
contacto y el caso destacado de Aurexir.

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
configurar servicios adicionales. El formulario mostrará un aviso de entrega
no disponible hasta que se configuren las credenciales SMTP.

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
| `ENVIRONMENT` | `development`, `staging` o `production` |
| `LOG_LEVEL` | Nivel de registros de la aplicación |
| `CONTACT_RECIPIENT_EMAIL` | Destinatario interno del formulario (fijo en `jriera@gozsyl.cloud`) |
| `SMTP_HOST` | Servidor SMTP utilizado por el formulario de contacto |
| `SMTP_PORT` | Puerto SMTP (`465` para Hostinger con SSL) |
| `SMTP_USERNAME` | Usuario de autenticación SMTP |
| `SMTP_PASSWORD` | Contraseña o clave de aplicación SMTP |
| `SMTP_FROM_EMAIL` | Remitente autorizado por el proveedor SMTP |
| `SMTP_SECURITY` | Seguridad SMTP: `starttls`, `ssl` o `none` |
| `SMTP_TIMEOUT_SECONDS` | Tiempo máximo de conexión y envío |

El formulario valida los campos en el servidor, usa protección CSRF, un campo
señuelo y límite de intentos. El destinatario no se acepta desde el navegador:
siempre se normaliza a `jriera@gozsyl.cloud`. El correo del visitante se utiliza
solo como `Reply-To`.

Para habilitar la entrega real, configura en el despliegue el host, puerto,
usuario y contraseña SMTP del proveedor de correo de `gozsyl.cloud`. La
configuración actual de Hostinger usa `smtp.hostinger.com`, puerto `465` y
`SMTP_SECURITY=ssl`; también admite `587` con `starttls`. El valor de
`SMTP_FROM_EMAIL` debe ser una dirección que el proveedor permita usar como
remitente.

## Comandos

```bash
npm run dev        # FastAPI + Tailwind con recarga automática
npm run build:css  # genera la hoja CSS minificada
```

## Rutas públicas

| Ruta | Descripción |
|---|---|
| `GET /` | Página principal en español |
| `GET /en` | Página principal en inglés |
| `GET /acerca` | Información sobre Gozsyl en español |
| `GET /en/about` | Información sobre Gozsyl en inglés |
| `GET/POST /contacto` | Formulario de contacto en español |
| `GET/POST /en/contact` | Formulario de contacto en inglés |
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
