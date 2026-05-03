# Sistema A - Web corporativa Gozsyl

Sitio web corporativo construido con FastAPI. Incluye landing minimalista,
blog con panel de administracion, autenticacion federada via **Keycloak**
(SSO + 2FA) y comunicacion cifrada con **Sistema B** (comparador de cuotas)
mediante **HashiCorp Vault Transit**.

> Proyecto academico de la materia *Desarrollo de Software Seguro*.
> Demuestra: autenticacion, autorizacion (RBAC), SSO/OIDC, 2FA, federacion
> de identidad y cifrado simetrico A → B.

---

## Stack

- **Python 3.11+** + **FastAPI** (Uvicorn en dev, Gunicorn + UvicornWorker en prod)
- **SQLAlchemy 2.0 async** + **Alembic** + **PostgreSQL**
- **Pydantic v2** + **pydantic-settings**
- **Jinja2** + **HTMX** + **Alpine.js** + **Tailwind CSS** (CDN, sin build step)
- **python-keycloak**, **hvac**, **httpx**, **python-jose**, **markdown**, **python-slugify**, **bleach**
- **loguru** para logging

---

## Requisitos

- Python 3.11 o superior
- PostgreSQL 14+
- Acceso a una instancia de Keycloak con un realm configurado
- Acceso a una instancia de Vault con el motor `transit` habilitado y una key creada

---

## Setup local

```bash
# 1) clonar el repo
git clone <repo-url>
cd sistema-a

# 2) crear y activar venv
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate

# 3) instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4) configurar variables de entorno
cp .env.example .env
# editar .env con valores reales

# 5) crear base de datos
createdb sistema_a    # o equivalente

# 6) correr migraciones
alembic upgrade head

# 7) levantar la app en desarrollo
uvicorn app.main:app --reload --port 8000
```

Abre http://localhost:8000.

---

## Variables de entorno

Todas estan documentadas en [`.env.example`](./.env.example). Resumen:

| Grupo | Variables |
|-------|-----------|
| App | `APP_URL`, `APP_NAME`, `APP_DESCRIPTION`, `ENVIRONMENT`, `LOG_LEVEL` |
| Sesion | `SECRET_KEY`, `SESSION_COOKIE_NAME`, `SESSION_MAX_AGE` |
| BD | `DATABASE_URL` (formato `postgresql+asyncpg://...`) |
| Keycloak | `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`, `KEYCLOAK_REDIRECT_URI`, `KEYCLOAK_POST_LOGOUT_URI` |
| Vault | `VAULT_URL`, `VAULT_TOKEN`, `VAULT_TRANSIT_KEY`, `VAULT_TRANSIT_MOUNT` |
| Sistema B | `SISTEMA_B_URL`, `SISTEMA_B_API_KEY`, `SISTEMA_B_TIMEOUT` |
| Uploads | `MAX_UPLOAD_SIZE_MB`, `ALLOWED_IMAGE_TYPES` |

> **Nunca** subas el archivo `.env` al repo. `SECRET_KEY` debe regenerarse para produccion (`python -c "import secrets; print(secrets.token_urlsafe(64))"`).

---

## Migraciones (Alembic)

```bash
# aplicar todas las migraciones pendientes
alembic upgrade head

# generar una nueva revision a partir de cambios en los modelos
alembic revision --autogenerate -m "descripcion del cambio"

# bajar una revision
alembic downgrade -1

# ver estado actual
alembic current
alembic history --verbose
```

La migracion inicial (`alembic/versions/2026_05_02_0001-0001_initial_schema.py`)
ya crea las tablas `users`, `posts` y `featured_sync_log`.

---

## Como correr en desarrollo

```bash
uvicorn app.main:app --reload --port 8000
```

- Docs OpenAPI (solo fuera de produccion): http://localhost:8000/api/docs
- Healthcheck: http://localhost:8000/healthz

### Estructura de rutas

| Ruta | Descripcion |
|------|-------------|
| `GET /` | Landing |
| `GET /acerca` | Acerca de |
| `GET /blog` | Listado paginado |
| `GET /blog/{slug}` | Detalle de post |
| `GET /sitemap.xml` | Sitemap dinamico |
| `GET /robots.txt` | Robots |
| `GET /auth/login` | Inicia OIDC con Keycloak |
| `GET /auth/callback` | Callback OIDC |
| `GET /auth/logout` | Cierra sesion local + Keycloak |
| `GET /admin` | Dashboard (requiere editor/admin) |
| `GET /admin/posts` | Listado admin |
| `GET /admin/posts/new` | Nuevo post |
| `POST /admin/posts` | Crear post |
| `GET /admin/posts/{id}/edit` | Editar |
| `POST /admin/posts/{id}` | Actualizar |
| `POST /admin/posts/{id}/delete` | Eliminar |

---

## Configuracion de Keycloak

Crea un cliente OIDC en tu realm con:

- **Client type:** OpenID Connect
- **Client ID:** el valor de `KEYCLOAK_CLIENT_ID` (por defecto `sistema-a`)
- **Client authentication:** ON (genera `client_secret`)
- **Valid redirect URIs:** `https://gozsyl.cloud/auth/callback` (y `http://localhost:8000/auth/callback` para dev)
- **Valid post logout redirect URIs:** `https://gozsyl.cloud/`
- **Web origins:** `https://gozsyl.cloud`

Roles soportados (cliente o realm):

- `user` — sesion basica, sin acceso a `/admin`
- `editor` — puede crear/editar sus propios posts
- `admin` — acceso completo a todos los posts

El **2FA / OTP** se configura en Keycloak (Authentication → Required Actions
→ "Configure OTP" o flujo browser con Conditional OTP).

---

## Configuracion de Vault

Habilita el motor `transit` y crea la key:

```bash
vault secrets enable transit
vault write -f transit/keys/featured-content-key
```

Crea una policy con permisos de cifrado/descifrado y emite un token con esa policy:

```hcl
# policy "sistema-a"
path "transit/encrypt/featured-content-key" { capabilities = ["update"] }
path "transit/decrypt/featured-content-key" { capabilities = ["update"] }
```

```bash
vault policy write sistema-a sistema-a.hcl
vault token create -policy=sistema-a -ttl=720h
```

Pon el token resultante en `VAULT_TOKEN`.

---

## Comunicacion A → B

Cuando un post se publica con la flag **Featured**, Sistema A:

1. Construye el payload `{post_id, title, slug, url, cover_image_url}`.
2. Lo serializa a JSON.
3. Lo cifra con `vault_service.encrypt()` (Vault Transit).
4. Lo envia con `POST {SISTEMA_B_URL}/api/featured-content` con `Authorization: Bearer <SISTEMA_B_API_KEY>`.
5. Registra el resultado en la tabla `featured_sync_log` (hash del payload, status, mensaje, timestamp).

Sistema B descifra el ciphertext con la **misma** transit key (Vault) y procesa
el contenido destacado.

---

## Seguridad (OWASP)

- **CSRF / SSO:** state aleatorio en `/auth/login` validado en `/auth/callback`.
- **XSS:** Jinja2 con autoescape y Markdown sanitizado con bleach (whitelist).
- **SQL injection:** SQLAlchemy ORM, sin SQL crudo.
- **Headers:** `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`,
  `Referrer-Policy strict-origin-when-cross-origin`, CSP estricta, HSTS en produccion.
- **Cookies:** `HttpOnly`, `SameSite=Lax`, `Secure` en prod (via `https_only`).
- **Secretos:** todos via env, jamas hardcoded.
- **Logging:** loguru con nivel configurable, captura logs estandar.

---

## Despliegue en EasyPanel

### Opcion A — Build desde repo Git

1. Crea un nuevo servicio **App** en EasyPanel.
2. Conecta tu repositorio.
3. Tipo de build: **Dockerfile** (apunta al `Dockerfile` del proyecto).
4. Define las variables de entorno en la pestania **Environment**
   (copia las de `.env.example` con valores reales).
5. Define el **Mount/Volume** si vas a permitir uploads locales en
   `app/static/uploads`.
6. Expone el puerto **8000**.
7. Configura el dominio: `https://gozsyl.cloud` y habilita HTTPS (Let's Encrypt).
8. (Opcional) crea un servicio **PostgreSQL** en el mismo proyecto y
   apunta `DATABASE_URL` a `postgresql+asyncpg://USER:PASS@<service>:5432/sistema_a`.

### Opcion B — Imagen pre-construida

```bash
docker build -t sistema-a:latest .
docker tag sistema-a:latest registry.example.com/sistema-a:latest
docker push registry.example.com/sistema-a:latest
```

Despues, en EasyPanel: **App → Source: Image**, pega la URL de la imagen y
configura las mismas variables.

### Migraciones en produccion

EasyPanel permite ejecutar comandos one-shot en el servicio. Tras desplegar:

```bash
alembic upgrade head
```

Si prefieres automatizarlo, agrega un *pre-deploy hook* o un container `init`
que ejecute `alembic upgrade head` antes de levantar Gunicorn.

### Healthcheck

El `Dockerfile` ya incluye un `HEALTHCHECK` contra `/healthz`. EasyPanel lo
respetara para reinicios automaticos.

---

## Licencia

Proyecto academico — uso interno Gozsyl.
