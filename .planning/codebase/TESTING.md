# Testing Patterns

**Analysis Date:** 2026-03-19

## Test Framework

**Runner:**
- Django `manage.py test` (unittest-based) on Python 3.12.
- Config: `taylor_learns/settings.py` (default Django test behavior) and CI workflow `.github/workflows/tests.yml`.

**Assertion Library:**
- `django.test.TestCase` / `django.test.SimpleTestCase` assertions from `unittest` style (examples in `apps/web/tests/test_basic_views.py`, `apps/web/tests/test_markdown_tags.py`).

**Run Commands:**
```bash
make test                              # Run all Django tests in container
make test ARGS='apps.web.tests.test_basic_views --keepdb'  # Run targeted module
uv run manage.py test                  # Native test run without make
```

## Test File Organization

**Location:**
- Use separate per-app test packages under `apps/<app>/tests/` (examples: `apps/web/tests/`, `apps/gadgets/tests/`, `apps/api/tests/`).

**Naming:**
- Use `test_*.py` naming for test modules (examples: `apps/web/tests/test_navigation_templates.py`, `apps/gadgets/tests/test_sync_gadgets_command.py`).
- Use `Test...` class naming and `test_...` method naming consistently.

**Structure:**
```
apps/
  web/tests/
    base.py
    test_basic_views.py
    test_markdown_tags.py
  gadgets/tests/
    test_create_gadget_command.py
    test_visibility_controls.py
```

## Test Structure

**Suite Organization:**
```typescript
class TestBasicViews(TestCase):
    def test_landing_page(self):
        self._assert_200(reverse("web:home"))

    def _assert_200(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
```

**Patterns:**
- Setup pattern: use `setUp`/`setUpClass` helpers to share clients and authenticated users (example: `apps/web/tests/base.py`).
- Teardown pattern: rely on `TestCase` transactional reset; for filesystem operations, use context managers like `TemporaryDirectory` (example: `apps/gadgets/tests/test_create_gadget_command.py`).
- Assertion pattern: favor semantic assertions (`assertContains`, `assertRedirects`, `assertNotContains`, `assertLogs`) over generic boolean checks (examples in `apps/web/tests/test_basic_views.py`).

## Mocking

**Framework:** `unittest.mock.patch`.

**Patterns:**
```typescript
@patch("apps.gadgets.management.commands.sync_gadgets.sync_all_gadgets")
def test_sync_gadgets_forwards_options_to_service(self, mock_sync_all_gadgets):
    mock_sync_all_gadgets.return_value = {"discovered": 0, "created": 0, "updated": 0, "synced": 0, "skipped": 0, "failed": 0}
    call_command("sync_gadgets", "--dry-run")
    mock_sync_all_gadgets.assert_called_once()
```

**What to Mock:**
- External service boundaries and side-effect-heavy collaborators (examples: patching metadata root resolution in `apps/web/tests/test_meta_tags.py`, command service call in `apps/gadgets/tests/test_sync_gadgets_command.py`).

**What NOT to Mock:**
- Core Django request/response lifecycle and ORM behavior in integration-style tests (examples: real client/DB use in `apps/web/tests/test_basic_views.py`, `apps/gadgets/tests/test_visibility_controls.py`).

## Fixtures and Factories

**Test Data:**
```typescript
GadgetSource.objects.create(
    slug="tmux-dojo",
    repo_full_name="bluestemso/tmux-dojo",
    is_hidden=True,
)
```

**Location:**
- No dedicated factory/fixture framework detected; create data inline per test module (examples: `apps/gadgets/tests/test_visibility_controls.py`, `apps/web/tests/base.py`).

## Coverage

**Requirements:** None enforced in repository config (no coverage target in `pyproject.toml`, `Makefile`, or `.github/workflows/tests.yml`).

**View Coverage:**
```bash
Not configured in repository; add a coverage tool command before relying on coverage gates.
```

## Test Types

**Unit Tests:**
- Pure helper/template/tag checks with `SimpleTestCase` and no DB (examples: `apps/web/tests/test_template_class_guards.py`, `apps/web/tests/test_navigation_templates.py`).

**Integration Tests:**
- Django client and ORM-backed endpoint behavior with `TestCase` (examples: `apps/web/tests/test_basic_views.py`, `apps/api/tests/test_schema.py`).

**E2E Tests:**
- Not used; no Playwright/Cypress/Selenium test suite detected for runtime browser E2E execution.

## Common Patterns

**Async Testing:**
```typescript
Not detected in current test suite; tests are synchronous Django/unittest style.
```

**Error Testing:**
```typescript
with self.assertRaises(CommandError):
    call_command("create_gadget", "focus-timer", title="Focus Timer")

with self.assertLogs("django.request", level="WARNING"):
    response = self.client.get("/simulate_error/")
```

---

*Testing analysis: 2026-03-19*
