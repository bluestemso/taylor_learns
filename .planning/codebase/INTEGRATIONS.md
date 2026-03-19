# External Integrations

**Analysis Date:** 2026-03-19

## APIs & External Services

**AI & Model Providers:**
- OpenAI models through LiteLLM routing - powers chat completions and agents
  - SDK/Client: `litellm`, `openai`, `pydantic-ai` declared in `pyproject.toml`
  - Auth: `OPENAI_API_KEY` in `taylor_learns/settings.py`
- Optional local Ollama endpoint - alternate model backend
  - SDK/Client: LiteLLM provider mapping in `taylor_learns/settings.py`
  - Auth: no token required by default; endpoint configured by `OLLAMA_API_BASE`

**Source Code Discovery/Sync:**
- GitHub REST API - discovers and syncs gadget repos in `apps/gadgets/sync.py`
  - SDK/Client: `httpx.Client` with `base_url="https://api.github.com"`
  - Auth: `GADGETS_GITHUB_TOKEN` in `taylor_learns/settings.py`

**Weather & Geocoding:**
- OpenStreetMap Nominatim - geocoding in `apps/ai/tools/weather.py`
  - SDK/Client: `requests`
  - Auth: none detected
- Open-Meteo API - weather lookup in `apps/ai/tools/weather.py`
  - SDK/Client: `httpx.AsyncClient`
  - Auth: none detected

**Human Verification:**
- Cloudflare Turnstile verify API - signup captcha validation in `apps/users/forms.py`
  - SDK/Client: `requests.post` to Turnstile endpoint
  - Auth: `TURNSTILE_SECRET` / public key from `TURNSTILE_KEY` in `taylor_learns/settings.py`

## Data Storage

**Databases:**
- PostgreSQL (local docker and production DB URL)
  - Connection: `DATABASE_URL` or `DJANGO_DATABASE_*` vars in `taylor_learns/settings.py`
  - Client: Django ORM + `psycopg2-binary`

**File Storage:**
- Local filesystem default in `taylor_learns/settings.py` (`FileSystemStorage`)
- Optional S3-compatible object storage (Cloudflare R2 pattern) via `apps/web/storage_backends.py`
  - Connection/Auth vars: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`

**Caching:**
- Redis cache backend in `taylor_learns/settings.py`
- Redis also used for Celery broker/result backend and Channels layer (`CELERY_BROKER_URL`, `CHANNEL_LAYERS` in `taylor_learns/settings.py`)

## Authentication & Identity

**Auth Provider:**
- Django Allauth (email/password + Google social login + MFA) configured in `taylor_learns/settings.py`
  - Implementation: session auth for web, allauth headless URLs in `taylor_learns/urls.py`, Google provider credentials via `GOOGLE_CLIENT_ID` and `GOOGLE_SECRET_ID`

## Monitoring & Observability

**Error Tracking:**
- Sentry (optional, DSN-driven) initialized in `taylor_learns/settings.py`

**Logs:**
- Python logging to console with env-controlled levels in `taylor_learns/settings.py`
- CI/CD workflow logs in `.github/workflows/tests.yml`, `.github/workflows/build_frontend.yml`, and `.github/workflows/deploy_coolify.yml`

## CI/CD & Deployment

**Hosting:**
- Coolify deployment flow triggered by GitHub Actions in `.github/workflows/deploy_coolify.yml`
- Container image published to GHCR (`ghcr.io/bluestemso/taylor_learns`) via same workflow
- Kamal deployment configuration also present in `config/deploy.yml`

**CI Pipeline:**
- GitHub Actions test/build/deploy workflows in `.github/workflows/tests.yml`, `.github/workflows/build_frontend.yml`, and `.github/workflows/deploy_coolify.yml`

## Environment Configuration

**Required env vars:**
- Core app/security: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` in `taylor_learns/settings.py`
- Database/cache: `DATABASE_URL` (or `DJANGO_DATABASE_*`), `REDIS_URL`/`REDIS_TLS_URL` in `taylor_learns/settings.py`
- Auth/integrations: `GOOGLE_CLIENT_ID`, `GOOGLE_SECRET_ID`, `TURNSTILE_KEY`, `TURNSTILE_SECRET`, `GADGETS_GITHUB_TOKEN`
- AI: `OPENAI_API_KEY`, `DEFAULT_LLM_MODEL`, `DEFAULT_AGENT_MODEL`, `OLLAMA_API_BASE`
- Storage/observability: `USE_S3_MEDIA`, `AWS_*`, `SENTRY_DSN`

**Secrets location:**
- Local development: `.env` file (present at repo root)
- CI deployment: GitHub Actions repository secrets referenced in `.github/workflows/deploy_coolify.yml`
- Kamal-based deploy path: secret keys listed in `config/deploy.yml` and external `.kamal/secrets` referenced by `scripts/sync_prod_db.sh`

## Webhooks & Callbacks

**Incoming:**
- Not detected in application URL routing (`taylor_learns/urls.py`, `apps/*/urls.py`)

**Outgoing:**
- Coolify deploy webhook trigger from CI using `COOLIFY_DEPLOY_WEBHOOK_URL` in `.github/workflows/deploy_coolify.yml`

---

*Integration audit: 2026-03-19*
