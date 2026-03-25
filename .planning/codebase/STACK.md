# Technology Stack

**Analysis Date:** 2026-03-19

## Languages

**Primary:**
- Python 3.12 - Django backend and app logic in `taylor_learns/settings.py`, `apps/`, and `manage.py`

**Secondary:**
- TypeScript 5.9 and JavaScript (ES modules) - front-end assets and API client in `assets/javascript/`, `vite.config.ts`, and `api-client/`
- HTML (Django templates) - server-rendered UI in `templates/` and `apps/*/templates/`

## Runtime

**Environment:**
- Python runtime pinned to 3.12 via `.python-version` and `pyproject.toml`
- Node runtime pinned in CI and container builds at Node 22 via `.github/workflows/build_frontend.yml` and `Dockerfile.vite`

**Package Manager:**
- Python: `uv` with lockfile workflows (`uv.lock`, `pyproject.toml`, `Makefile` targets `uv`, `uv-sync`)
- JavaScript: `npm` with lockfile (`package-lock.json`) and local package dependency (`api-client/package.json`)
- Lockfile: present (`uv.lock`, `package-lock.json`)

## Frameworks

**Core:**
- Django 5.2.x - main web framework and app configuration in `pyproject.toml` and `taylor_learns/settings.py`
- Wagtail 7.2.x - CMS/content layer configured in `taylor_learns/settings.py` and routed via `taylor_learns/urls.py`
- Django REST Framework - API layer and schema generation in `taylor_learns/settings.py` and `apps/api/`
- Channels + Daphne - ASGI/WebSocket support in `taylor_learns/asgi.py` and `taylor_learns/channels_urls.py`

**Testing:**
- Django test runner - test execution via `make test` in `Makefile` and CI in `.github/workflows/tests.yml`

**Build/Dev:**
- Vite 8 - front-end dev server and production builds in `vite.config.ts` and `package.json`
- Tailwind CSS 4 + DaisyUI 5 - styling pipeline in `package.json`, `tailwind.config.js`, and `postcss.config.js`
- Ruff - formatting and linting in `pyproject.toml` and `Makefile` (`ruff-format`, `ruff-lint`)

## Key Dependencies

**Critical:**
- `django-allauth` - auth, social auth, MFA, and headless auth URLs configured in `taylor_learns/settings.py` and `taylor_learns/urls.py`
- `celery` + `django-celery-beat` - background jobs and scheduler in `taylor_learns/settings.py`, `taylor_learns/celery.py`, and `apps/gadgets/tasks.py`
- `channels` + `channels_redis` - channel layer and async transport support in `taylor_learns/asgi.py` and `taylor_learns/settings.py`

**Infrastructure:**
- `psycopg2-binary` - PostgreSQL driver declared in `pyproject.toml`
- `redis` - cache + Celery broker backend configured in `taylor_learns/settings.py`
- `django-storages` + `boto3` - S3-compatible media storage integration in `apps/web/storage_backends.py` and `taylor_learns/settings.py`
- `sentry-sdk[django]` - error tracking bootstrapped in `taylor_learns/settings.py`

## Configuration

**Environment:**
- Uses `django-environ` with `.env` loading from `taylor_learns/settings.py` (`env.read_env(...)`)
- `.env` and `.env.example` files are present at project root for local configuration
- Required integration/config vars are consumed in `taylor_learns/settings.py` (database, redis, auth, storage, observability)

**Build:**
- Python/dependency config in `pyproject.toml` and `uv.lock`
- JS build config in `package.json`, `vite.config.ts`, `tailwind.config.js`, and `postcss.config.js`
- Container build/runtime config in `Dockerfile.dev`, `Dockerfile.vite`, `Dockerfile.web`, and `docker-compose.yml`

## Platform Requirements

**Development:**
- Docker + Docker Compose based workflow (`docker-compose.yml`, `Makefile`, `README.md`)
- Native workflow also supported with `uv` and `npm` (`README.md`)

**Production:**
- Containerized Django deployment using `Dockerfile.web`
- Coolify deployment target triggered from GitHub Actions in `.github/workflows/deploy_coolify.yml`
- Alternative Kamal deployment config present in `config/deploy.yml`

---

*Stack analysis: 2026-03-19*
