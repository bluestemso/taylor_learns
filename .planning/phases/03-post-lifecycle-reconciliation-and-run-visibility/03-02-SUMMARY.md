---
phase: 03-post-lifecycle-reconciliation-and-run-visibility
plan: 02
subsystem: api
tags: [django, bluesky, wagtail, admin, sync]
requires:
  - phase: 03-01
    provides: lifecycle reconciliation counters including removed
provides:
  - Persisted Bluesky sync run records with deterministic counters and timestamps
  - Admin run history visibility by source and completion order
  - Command output parity for imported/updated/removed/skipped/failed counters
affects: [phase-04-scheduling, bluesky-sync-operations]
tech-stack:
  added: []
  patterns:
    - Persist run-level operational telemetry directly from sync orchestrator
    - Keep operator CLI output order aligned with persisted counter contract
key-files:
  created:
    - apps/bluesky/migrations/0004_blueskysyncrun.py
    - apps/bluesky/tests/test_sync_run_visibility.py
  modified:
    - apps/bluesky/models.py
    - apps/bluesky/admin.py
    - apps/bluesky/sync.py
    - apps/bluesky/management/commands/sync_bluesky.py
    - apps/bluesky/tests/test_sync_bluesky_command.py
key-decisions:
  - "Persist one BlueskySyncRun row per run_sync invocation using returned counters as the source of truth."
  - "Use a source-scoped descending completion index for admin/query visibility while keeping name under database limits."
patterns-established:
  - "Run visibility contract: dict counters and persisted counters use the same key set and order semantics."
requirements-completed: [LIFE-03]
duration: 7 min
completed: 2026-03-20
---

# Phase 3 Plan 2: Run Visibility Summary

**Bluesky sync now persists per-run imported/updated/removed/skipped/failed counters and exposes the same contract in admin and command output.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-20T16:09:51Z
- **Completed:** 2026-03-20T16:17:18Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Added RED tests for run-history persistence and deterministic `sync_bluesky` counter output ordering.
- Implemented `BlueskySyncRun` model + migration + admin registration with source/completion visibility columns.
- Persisted run outcomes from `run_sync` and aligned command output with the removed-inclusive counter contract.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add failing run-visibility tests for model persistence and command output** - `d1a60d2` (test)
2. **Task 2: Implement BlueskySyncRun model, migration, and admin registration** - `a5aa476` (feat)
3. **Task 3: Persist run outcomes from sync and align command output contract** - `517e4a4` (feat)

## Files Created/Modified
- `apps/bluesky/tests/test_sync_run_visibility.py` - TDD contracts for persisted run rows and admin registration/list display.
- `apps/bluesky/tests/test_sync_bluesky_command.py` - Deterministic output expectation including `removed`.
- `apps/bluesky/models.py` - `BlueskySyncRun` model with run counters and source-ordered index.
- `apps/bluesky/migrations/0004_blueskysyncrun.py` - Schema creation for run history table and index.
- `apps/bluesky/admin.py` - `BlueskySyncRunAdmin` registration with run visibility columns.
- `apps/bluesky/sync.py` - Run lifecycle persistence (`started_at`/`completed_at` + counter snapshot).
- `apps/bluesky/management/commands/sync_bluesky.py` - Operator output now includes `removed` in contract order.

## Decisions Made
- Persist run records inside `run_sync` so every invocation has a durable outcome row regardless of caller.
- Keep the counter shape as the single source contract across sync return payload, persisted rows, tests, and CLI output.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reduced run-history index name to satisfy Django/db identifier limits**
- **Found during:** Task 2
- **Issue:** Initial index name exceeded the 30-character database limit, blocking model checks.
- **Fix:** Renamed index to `bluesky_sr_src_comp_idx` in model and migration.
- **Files modified:** `apps/bluesky/models.py`, `apps/bluesky/migrations/0004_blueskysyncrun.py`
- **Verification:** `make test ARGS='apps.bluesky.tests.test_sync_run_visibility'`
- **Committed in:** `a5aa476` (part of task commit)

**2. [Rule 3 - Blocking] Persisted run rows during Task 2 to satisfy verification gate**
- **Found during:** Task 2
- **Issue:** Task 2 verification target (`test_sync_run_visibility`) asserted run persistence before Task 3, causing blocking failure.
- **Fix:** Added `BlueskySyncRun.objects.create(...)` in `run_sync` using current counters and timestamps.
- **Files modified:** `apps/bluesky/sync.py`
- **Verification:** `make test ARGS='apps.bluesky.tests.test_sync_run_visibility'`
- **Committed in:** `a5aa476` (part of task commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both deviations were required to pass the plan's explicit verification gates; no architectural scope change.

## Issues Encountered
- None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 requirements are fully covered; run history visibility and lifecycle reconciliation are both in place.
- Ready for Phase 4 planning/execution (scheduled sync and concurrency safety).

## Self-Check: PASSED

---
*Phase: 03-post-lifecycle-reconciliation-and-run-visibility*
*Completed: 2026-03-20*
