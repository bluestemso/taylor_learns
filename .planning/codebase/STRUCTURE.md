# Codebase Structure

**Analysis Date:** 2026-03-19

## Directory Layout

```text
[project-root]/
├── taylor_learns/        # Project package: settings, URL composition, ASGI/WSGI, Celery
├── apps/                 # Domain apps (web, users, chat, content, gadgets, api, ai, etc.)
├── templates/            # Global Django templates and app-level UI composition
├── assets/               # Frontend source assets built by Vite
├── static/               # Built static output (including Vite manifest/assets)
├── api-client/           # Generated OpenAPI TypeScript client consumed by frontend
├── gadgets/              # Published gadget artifacts served by gadgets app
├── scripts/              # Project maintenance/verification scripts
├── .github/workflows/    # CI/CD and deployment workflows
└── .planning/codebase/   # Generated architecture/quality mapping artifacts
```

## Directory Purposes

**`apps/`:**
- Purpose: Main application code organized by bounded domain.
- Contains: `views.py`, `urls.py`, `models.py`, `forms.py`, `tasks.py`, `management/commands/`, `tests/`, plus feature-specific modules.
- Key files: `apps/web/views.py`, `apps/users/models.py`, `apps/chat/consumers.py`, `apps/gadgets/sync.py`, `apps/content/models.py`.

**`taylor_learns/`:**
- Purpose: Runtime composition and global framework configuration.
- Contains: settings, root URLConf, ASGI/WSGI, channels URL aggregation, Celery bootstrap.
- Key files: `taylor_learns/settings.py`, `taylor_learns/urls.py`, `taylor_learns/asgi.py`, `taylor_learns/channels_urls.py`, `taylor_learns/celery.py`.

**`templates/`:**
- Purpose: Global template hierarchy and reusable partials.
- Contains: base layouts, app screens, account/auth templates, component includes.
- Key files: `templates/web/base.html`, `templates/content/base.html`, `templates/chat/single_chat_streaming.html`, `templates/dashboard/user_dashboard.html`.

**`assets/`:**
- Purpose: Source JS/TS/CSS for browser functionality.
- Contains: entrypoints and feature bundles under `assets/javascript/` and style entrypoints under `assets/styles/`.
- Key files: `assets/javascript/site.js`, `assets/javascript/app.js`, `assets/javascript/chat/ws_initialize.ts`, `assets/styles/site-tailwind.css`.

**`api-client/`:**
- Purpose: Local package for generated API client code.
- Contains: OpenAPI-generated runtime and index files.
- Key files: `api-client/index.ts`, `api-client/runtime.ts`, `api-client/package.json`.

## Key File Locations

**Entry Points:**
- `manage.py`: CLI command entry for Django management tasks.
- `taylor_learns/urls.py`: Root HTTP route registration.
- `taylor_learns/asgi.py`: ASGI protocol router for HTTP and websocket traffic.
- `taylor_learns/wsgi.py`: WSGI entry for synchronous server deployments.
- `taylor_learns/celery.py`: Celery application entry for workers/beat.

**Configuration:**
- `taylor_learns/settings.py`: Django, DB, auth, cache, Channels, Celery, and integration config.
- `pyproject.toml`: Python dependencies and Ruff config.
- `package.json`: Frontend dependency and script definitions.
- `vite.config.ts`: Frontend build inputs/outputs and aliases.
- `Makefile`: Unified developer command surface for Docker/native workflows.

**Core Logic:**
- `apps/content/models.py`: Wagtail page types and content model definitions.
- `apps/chat/sessions.py`: Chat/agent orchestration and LLM interaction state.
- `apps/chat/consumers.py`: WebSocket streaming and server-to-client message rendering.
- `apps/gadgets/sync.py`: GitHub repository discovery and gadget publishing pipeline.
- `apps/web/middleware/subdomains.py`: Host-based URLConf switching into gadgets app.

**Testing:**
- `apps/web/tests/`: Template, routing, and view behavior tests.
- `apps/gadgets/tests/`: Gadget visibility/sync command coverage.
- `apps/api/tests/`: API schema filtering checks.

## Naming Conventions

**Files:**
- `snake_case.py` for Python modules: `apps/dashboard/services.py`, `apps/web/context_processors.py`.
- Conventional Django module names per app: `urls.py`, `views.py`, `models.py`, `admin.py`, `apps.py`.
- Test modules prefixed with `test_`: `apps/web/tests/test_basic_views.py`.

**Directories:**
- Domain-oriented lowercase app directories: `apps/web`, `apps/users`, `apps/chat`, `apps/gadgets`.
- Django convention subdirectories where relevant: `management/commands/`, `migrations/`, `templatetags/`, `tests/`.

## Where to Add New Code

**New Feature:**
- Primary code: Add/extend an existing domain app under `apps/<domain>/` (for example `apps/chat/`, `apps/gadgets/`, `apps/users/`) and wire routes from `apps/<domain>/urls.py` into `taylor_learns/urls.py` when needed.
- Tests: Add tests in the same app's `apps/<domain>/tests/` folder (pattern shown in `apps/web/tests/` and `apps/gadgets/tests/`).

**New Component/Module:**
- Implementation: Put user-facing templates in `templates/<domain>/` (or app-local template paths like `apps/gadgets/templates/gadgets/` when coupled to an app), and add supporting view logic in `apps/<domain>/views.py`.

**Utilities:**
- Shared helpers: Place cross-domain helpers in `apps/utils/` when generic (for example base models in `apps/utils/models.py`); keep domain-specific helpers inside their app (for example `apps/web/meta.py`, `apps/api/helpers.py`, `apps/chat/utils.py`).

## Special Directories

**`apps/*/migrations/`:**
- Purpose: Django migration history for each app.
- Generated: Yes.
- Committed: Yes.

**`static/.vite/`:**
- Purpose: Vite manifest and build metadata for `django-vite` asset resolution.
- Generated: Yes.
- Committed: Yes (present in repository alongside built static output).

**`node_modules/`:**
- Purpose: Local npm dependency installation.
- Generated: Yes.
- Committed: No.

**`.planning/codebase/`:**
- Purpose: Mapping artifacts consumed by GSD planning/execution tools.
- Generated: Yes.
- Committed: Yes (intended project documentation output).

---

*Structure analysis: 2026-03-19*
