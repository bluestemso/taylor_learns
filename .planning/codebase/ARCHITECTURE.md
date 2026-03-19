# Architecture

**Analysis Date:** 2026-03-19

## Pattern Overview

**Overall:** Modular Django monolith with app-by-domain boundaries and mixed sync/async delivery.

**Key Characteristics:**
- URL composition at project level in `taylor_learns/urls.py` delegates to app URLConfs such as `apps/web/urls.py`, `apps/users/urls.py`, and `apps/chat/urls.py`.
- Most user-facing flows use server-rendered templates (for example `templates/web/base.html`, `templates/content/*.html`) with progressive enhancement via HTMX/Alpine assets in `assets/javascript/`.
- Real-time chat is isolated behind ASGI + Channels entry points in `taylor_learns/asgi.py`, `taylor_learns/channels_urls.py`, and `apps/chat/consumers.py`.

## Layers

**Routing and entry layer:**
- Purpose: Accept HTTP/WebSocket traffic and route into app modules.
- Location: `manage.py`, `taylor_learns/wsgi.py`, `taylor_learns/asgi.py`, `taylor_learns/urls.py`, `apps/chat/routing.py`.
- Contains: URL registration, ASGI protocol routing, app bootstrapping.
- Depends on: Django URL system, Channels router, app URL modules.
- Used by: Runtime server processes (Django/ASGI workers) and tests.

**Presentation layer (views + templates):**
- Purpose: Build HTML responses and page context for browser clients.
- Location: `apps/web/views.py`, `apps/users/views.py`, `apps/dashboard/views.py`, `apps/support/views.py`, `apps/chat/views.py`, templates in `templates/` and `apps/gadgets/templates/`.
- Contains: Function-based views, TemplateResponse/render calls, template fragments.
- Depends on: Forms/models/helpers/context processors.
- Used by: Browser HTTP requests routed from `taylor_learns/urls.py`.

**Domain and data layer (models + services):**
- Purpose: Represent persistent entities and domain-specific logic.
- Location: `apps/users/models.py`, `apps/chat/models.py`, `apps/content/models.py`, `apps/gadgets/models.py`, `apps/dashboard/services.py`, `apps/gadgets/sync.py`.
- Contains: ORM models, Wagtail page models, query/aggregation services, gadget synchronization workflows.
- Depends on: Django ORM, Wagtail model APIs, external HTTP clients for sync.
- Used by: Views, tasks, admin actions, websocket sessions.

**Async and integration layer (tasks + websocket sessions):**
- Purpose: Handle long-running/background work and streaming conversational flows.
- Location: `apps/chat/tasks.py`, `apps/gadgets/tasks.py`, `apps/chat/sessions.py`, `apps/chat/consumers.py`, `taylor_learns/celery.py`.
- Contains: Celery tasks, session orchestration, AI streaming token handling.
- Depends on: Redis/Celery configuration in `taylor_learns/settings.py`, LLM and agent abstractions in `apps/ai/agents.py`.
- Used by: WebSocket consumers and periodic/manual task triggers.

## Data Flow

**HTTP page request flow:**

1. Request enters project URL config in `taylor_learns/urls.py` and is dispatched to an app URL module such as `apps/web/urls.py`.
2. View resolves data from models/services (for example `apps/web/views.py` querying `apps/content/models.py` or `apps/dashboard/views.py` using `apps/dashboard/services.py`).
3. Response renders templates rooted at `templates/web/base.html` and related includes, with client behavior hydrated by Vite assets configured in `vite.config.ts`.

**WebSocket chat flow:**

1. Browser receives websocket URL from `apps/chat/views.py` using helpers in `apps/web/meta.py` and connects to routes in `apps/chat/routing.py`.
2. ASGI router in `taylor_learns/asgi.py` sends socket traffic to consumers in `apps/chat/consumers.py`.
3. Session objects in `apps/chat/sessions.py` persist messages in `apps/chat/models.py`, stream model/agent output, and push HTML fragments back to HTMX components.

**Gadget sync flow:**

1. Sync starts via management command `apps/gadgets/management/commands/sync_gadgets.py`, Celery task `apps/gadgets/tasks.py`, or admin action in `apps/gadgets/admin.py`.
2. Core orchestration in `apps/gadgets/sync.py` discovers repositories, downloads tarballs, validates required files, and publishes into filesystem path `gadgets/<slug>/`.
3. Metadata and status persist in `apps/gadgets/models.py`, then gadget pages are served through `apps/gadgets/views.py`.

**State Management:**
- Persistent state is in Django/Postgres models (`apps/*/models.py`), CMS state in Wagtail page models (`apps/content/models.py`), ephemeral chat stream state in `ChatSessionBase` instances (`apps/chat/sessions.py`), and client UI state in HTMX/Alpine components from `assets/javascript/`.

## Key Abstractions

**Base timestamp model:**
- Purpose: Provide consistent `created_at`/`updated_at` fields.
- Examples: `apps/utils/models.py`, inherited by `apps/chat/models.py` and `apps/gadgets/models.py`.
- Pattern: Shared abstract base model.

**Chat session abstraction:**
- Purpose: Normalize message persistence and LLM/agent response generation for multiple chat types.
- Examples: `apps/chat/sessions.py` (`ChatSessionBase`, `ChatSession`, `AgentSession`).
- Pattern: Abstract base class + specialized subclasses selected by enum.

**Subdomain URL switching abstraction:**
- Purpose: Route gadgets hostnames to an alternate URLConf without separate project.
- Examples: `apps/web/middleware/subdomains.py`, `apps/gadgets/urls.py`.
- Pattern: Middleware-based URLConf override (`request.urlconf`).

**AI agent toolset abstraction:**
- Purpose: Attach constrained tools to specific agent types.
- Examples: `apps/ai/agents.py`, `apps/ai/tools/weather.py`, `apps/ai/tools/admin_db.py`, `apps/ai/tools/email.py`.
- Pattern: Agent factory + typed toolsets.

## Entry Points

**Django management entry:**
- Location: `manage.py`
- Triggers: CLI commands (`uv run manage.py ...` or Make targets).
- Responsibilities: Process startup and management command dispatch.

**HTTP URL entry:**
- Location: `taylor_learns/urls.py`
- Triggers: All HTTP requests.
- Responsibilities: Compose app routes, admin/cms, schema docs, and static media serving in debug contexts.

**ASGI/WebSocket entry:**
- Location: `taylor_learns/asgi.py`
- Triggers: ASGI server handling HTTP + websocket protocols.
- Responsibilities: Protocol routing and websocket middleware stack initialization.

**Celery worker entry:**
- Location: `taylor_learns/celery.py`
- Triggers: Celery worker/beat process start.
- Responsibilities: Celery app configuration and autodiscovery of `@shared_task` functions.

## Error Handling

**Strategy:** Guard at boundaries and degrade gracefully to safe responses.

**Patterns:**
- View-level graceful fallbacks such as returning empty/home fallback state in `apps/web/views.py` and 404 guards in `apps/gadgets/views.py`.
- Task/session exception capture with status persistence or user-visible fallback, for example `apps/gadgets/sync.py` and `apps/chat/consumers.py`.

## Cross-Cutting Concerns

**Logging:** Standard Django logging configured in `taylor_learns/settings.py` with named loggers (including AI-focused logger usage in `apps/chat/consumers.py` and `apps/ai/handlers.py`).
**Validation:** Input/form validation in Django forms and model constraints (`apps/users/forms.py`, `apps/gadgets/sync.py` required-file checks, model field constraints across `apps/*/models.py`).
**Authentication:** Session auth and allauth flows configured in `taylor_learns/settings.py`; access control enforced via decorators in views (`apps/users/views.py`, `apps/dashboard/views.py`, `apps/support/views.py`) and API permission composition in `apps/api/permissions.py`.

---

*Architecture analysis: 2026-03-19*
