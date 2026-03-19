# Coding Conventions

**Analysis Date:** 2026-03-19

## Naming Patterns

**Files:**
- Use `snake_case.py` for Python modules and test files (examples: `apps/web/template_checks.py`, `apps/web/tests/test_basic_views.py`).
- Use `snake_case` for Django app modules and command files (examples: `apps/gadgets/management/commands/sync_gadgets.py`, `apps/users/forms.py`).
- Use mixed JS file naming by folder convention: kebab-case for some dashboard assets (example: `assets/javascript/dashboard/dashboard-charts.js`) and snake_case for targeted entry points (example: `assets/javascript/chat/ws_initialize.ts`); keep naming consistent within the same folder.

**Functions:**
- Use `snake_case` for Python functions and methods (examples: `apps/web/views.py`, `apps/gadgets/sync.py`, `apps/web/templatetags/markdown_tags.py`).
- Use `camelCase` for JavaScript/TypeScript functions (examples: `getApiConfiguration` in `assets/javascript/api.js`, `initializeChatHandlers` in `assets/javascript/chat/ws_initialize.ts`).

**Variables:**
- Use `snake_case` for Python locals, kwargs, and module constants; use `UPPER_SNAKE_CASE` for constants (examples: `REQUIRED_GADGET_FILES` in `apps/gadgets/sync.py`, `SLUG_PATTERN` in `apps/gadgets/management/commands/create_gadget.py`).
- Use `camelCase` for JavaScript variables and object keys where idiomatic (examples: `serverBaseUrl` in `assets/javascript/api.js`, `chartData` in `assets/javascript/dashboard/dashboard-charts.js`).

**Types:**
- Use `PascalCase` for Python classes, dataclasses, and Django models (examples: `CustomUser` in `apps/users/models.py`, `UserDependencies` in `apps/ai/types.py`, `TestBasicViews` in `apps/web/tests/test_basic_views.py`).
- Use descriptive `Test...` class names for test suites (examples: `TestTemplateClassGuards` in `apps/web/tests/test_template_class_guards.py`, `TestSyncGadgetsCommand` in `apps/gadgets/tests/test_sync_gadgets_command.py`).

## Code Style

**Formatting:**
- Use Ruff as the canonical formatter and linter configuration source from `pyproject.toml`.
- Keep Python line length at 120 and indentation width at 4 as defined in `pyproject.toml`.
- Use double quotes for Python strings per Ruff format settings in `pyproject.toml`.
- Use semicolon-terminated statements and 2-space indentation for JS/TS to match current assets (examples: `assets/javascript/chat/ws_initialize.ts`, `assets/javascript/api.js`).

**Linting:**
- Run Ruff checks and auto-fixes with `ruff check --fix` and `ruff format` via `Makefile` targets `ruff-lint` and `ruff-format`.
- Keep pre-commit enabled via `.pre-commit-config.yaml`; it enforces Ruff and a custom template class guard (`scripts/check_template_classes.py`).
- Respect active Ruff rule families `E`, `F`, `I`, `UP`, `B`, and `SIM` defined in `pyproject.toml`.

## Import Organization

**Order:**
1. Python standard library imports first (examples: `json`, `tempfile` in `apps/gadgets/sync.py`).
2. Third-party imports second (examples: `httpx`, `django.*`, `markdown`, `nh3` in `apps/gadgets/sync.py` and `apps/web/templatetags/markdown_tags.py`).
3. Local app imports last, then explicit relative imports where appropriate (examples: `from apps.chat.models import Chat` in `apps/chat/views.py`, `from .gadgets import get_gadgets_url` in `apps/web/views.py`).

**Path Aliases:**
- Use Vite alias `@` mapped to `assets/javascript` for frontend imports, as declared in `vite.config.ts`.
- Use Django app absolute imports under `apps.` for cross-app Python imports (examples: `apps/users/forms.py`, `apps/chat/views.py`).

## Error Handling

**Patterns:**
- Raise explicit framework exceptions for request/control flow failures (examples: `Http404` in `apps/web/views.py`, `CommandError` in `apps/gadgets/management/commands/create_gadget.py`).
- Raise `forms.ValidationError` for user-input failures inside forms (example: `apps/users/forms.py`).
- For external integration flows, catch and persist failure state before returning structured status (example: broad catch in `apps/gadgets/sync.py` updates `last_sync_status` and `last_sync_error`).

## Logging

**Framework:** Python `logging` with Django `LOGGING` configuration in `taylor_learns/settings.py`.

**Patterns:**
- Use named loggers for domain areas when adding detailed operational logs (example: `logger = logging.getLogger("pegasus.ai")` in `apps/ai/handlers.py`).
- Use `assertLogs` in tests to validate warning/error behavior (examples: `apps/web/tests/test_basic_views.py`, `apps/gadgets/tests/test_visibility_controls.py`).

## Comments

**When to Comment:**
- Add comments for intent and operational constraints, not for obvious statements (examples: migration-check rationale in `apps/web/tests/test_missing_migrations.py`, tar extraction safety guard in `apps/gadgets/sync.py`).
- Keep short inline comments for framework workarounds and compatibility notes (examples: `taylor_learns/urls.py`, `vite.config.ts`).

**JSDoc/TSDoc:**
- Not detected as a formal requirement; use brief inline comments instead (examples: `assets/javascript/chat/ws_initialize.ts`, `assets/javascript/site.js`).

## Function Design

**Size:**
- Keep most view and utility functions compact and single-purpose (examples: `apps/web/views.py`, `apps/web/template_checks.py`).
- Use helper function extraction for larger workflows (example: `apps/gadgets/sync.py` separates fetch/validate/publish steps).

**Parameters:**
- Use keyword-only and typed parameters for service-layer APIs where branching behavior is complex (example: `sync_all_gadgets(*, dry_run, force, slug, repo_full_name, topics, owners)` in `apps/gadgets/sync.py`).
- Use typed request identifiers in view signatures where routing supplies IDs (example: `single_chat_streaming(request, chat_id: int)` in `apps/chat/views.py`).

**Return Values:**
- Return framework response objects from views (`render`, `TemplateResponse`, `HttpResponseRedirect`) in `apps/web/views.py` and `apps/chat/views.py`.
- Return structured dictionaries for internal service status handoff (example: sync status dicts in `apps/gadgets/sync.py`).

## Module Design

**Exports:**
- Use direct named function/class definitions per module; avoid wildcard exports (examples across `apps/*/*.py`).
- Keep template tags colocated in `templatetags` modules and register explicitly (example: `apps/web/templatetags/markdown_tags.py`).

**Barrel Files:**
- Python barrel-export pattern is not used; `__init__.py` files are present but minimal (examples: `apps/api/__init__.py`, `apps/web/tests/__init__.py`).

---

*Convention analysis: 2026-03-19*
