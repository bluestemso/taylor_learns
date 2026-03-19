---
status: resolved
trigger: "Investigate issue: bluesky-admin-source-settings-500"
created: 2026-03-19T21:57:18Z
updated: 2026-03-19T22:05:04Z
---

## Current Focus

hypothesis: The root cause has been fixed by applying bluesky migrations; awaiting real-workflow admin verification.
test: User validates `/admin/bluesky/blueskysourcesettings/` in browser session.
expecting: Admin changelist loads without HTTP 500.
next_action: archive resolved session and update knowledge base

## Symptoms

expected: Bluesky source settings admin page loads normally.
actual: Admin changelist endpoint returns a 500 every time.
errors: Django traceback shows `django.db.utils.ProgrammingError: relation "bluesky_blueskysourcesettings" does not exist` and startup warns `You have 2 unapplied migration(s)... app(s): bluesky`.
reproduction: Start app, log into admin, visit `/admin/bluesky/blueskysourcesettings/`.
started: Started after recent Phase 2 changes; route is always reproducible.

## Eliminated

## Evidence

- timestamp: 2026-03-19T21:57:43Z
  checked: .planning/debug/knowledge-base.md
  found: File does not exist yet, so there is no known-pattern candidate to test first.
  implication: Proceed with standard evidence gathering and fresh hypothesis testing.

- timestamp: 2026-03-19T21:58:03Z
  checked: apps/bluesky/models.py and apps/bluesky/admin.py
  found: Admin changelist queries BlueskySourceSettings model directly, which maps to table `bluesky_blueskysourcesettings`.
  implication: If that table is absent, admin list view will consistently fail with database ProgrammingError.

- timestamp: 2026-03-19T21:58:03Z
  checked: apps/bluesky/migrations/0001_initial.py and apps/bluesky/migrations/0002_blueskypostmap.py
  found: Migration `0001_initial` creates BlueskySourceSettings; `0002_blueskypostmap` depends on it and content migration.
  implication: The missing relation error is consistent with unapplied bluesky migrations rather than model/admin code defects.

- timestamp: 2026-03-19T21:58:28Z
  checked: migration state via `make manage ARGS='showmigrations bluesky'`
  found: Both bluesky migrations (`0001_initial`, `0002_blueskypostmap`) are unapplied.
  implication: Strongly confirms root cause is unapplied migrations causing missing table at runtime.

- timestamp: 2026-03-19T21:59:03Z
  checked: `make manage ARGS='migrate bluesky'`
  found: Migrations `bluesky.0001_initial` and `bluesky.0002_blueskypostmap` applied successfully.
  implication: Missing relation should now exist; issue should be resolved pending verification checks.

- timestamp: 2026-03-19T21:59:43Z
  checked: `make manage ARGS='showmigrations bluesky'`
  found: Both bluesky migrations now show as applied (`[X]`).
  implication: Database schema now includes tables required by Bluesky admin changelist.

- timestamp: 2026-03-19T21:59:43Z
  checked: `make test ARGS='apps.bluesky.tests.test_admin_source_settings'`
  found: Focused admin test module passed (6/6 tests).
  implication: Regression coverage for admin source settings behavior is green after migration application.

## Resolution

root_cause: Bluesky migrations that create `bluesky_blueskysourcesettings` were present but unapplied in the running database.
fix: Applied pending bluesky migrations to create required tables (`bluesky_blueskysourcesettings`, `bluesky_blueskypostmap`) in the local database.
verification: Verified schema state via `showmigrations`, passed focused admin test suite (`apps.bluesky.tests.test_admin_source_settings`), and user confirmed admin route is fixed in real workflow.
files_changed: []
