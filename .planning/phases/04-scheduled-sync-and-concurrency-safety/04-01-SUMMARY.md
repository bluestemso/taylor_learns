---
phase: 04-scheduled-sync-and-concurrency-safety
plan: 01
subsystem: sync
tags: [bluesky, celery, django-celery-beat, concurrency, lease-lock]

# Dependency graph
requires:
  - phase: 03-post-lifecycle-reconciliation-and-run-visibility
    provides: run_sync orchestration and BlueskySyncRun persistence counters
provides:
  - Scheduled Bluesky sync task wired into existing Celery beat bootstrap flow
  - Per-source DB lease lock to prevent overlapping run_sync execution
  - Requirement-level tests for scheduled parity and lock behavior
affects: [bluesky-sync, celery-beat, run-visibility]

# Tech tracking
tech-stack:
  added: []
  patterns: [single-flight lease lock in run_sync, scheduler configuration via SCHEDULED_TASKS]

key-files:
  created:
    - apps/bluesky/tasks.py
    - apps/bluesky/migrations/0005_blueskysourcesettings_sync_lock_fields.py
    - apps/bluesky/tests/test_scheduled_sync.py
    - apps/bluesky/tests/test_sync_concurrency.py
  modified:
    - apps/bluesky/sync.py
    - apps/bluesky/models.py
    - taylor_learns/settings.py

key-decisions:
  - "Put overlap lock acquisition/release inside run_sync so manual and scheduled triggers share one single-flight path."
  - "Use DB lease fields on BlueskySourceSettings instead of cache locking so behavior is deterministic across environments."

patterns-established:
  - "Scheduled task wrappers gate on settings flag and delegate to a single sync service function."
  - "Lease lock release is owner-safe using token match in finally."

requirements-completed: [SYNC-03, LIFE-04]

# Metrics
duration: 5 min
completed: 2026-03-20
---

# Phase 4 Plan 1: Scheduled Sync and Concurrency Safety Summary

**Bluesky scheduled sync now runs through Celery beat with a per-source lease lock in run_sync that skips overlap deterministically while preserving existing import/update/remove counters.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T17:27:56Z
- **Completed:** 2026-03-20T17:33:53Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments
- Added RED coverage for scheduled task gating/delegation and lock overlap semantics.
- Added persistent source lock token/expiry fields with migration and atomic compare-and-set acquisition in `run_sync`.
- Added `sync_bluesky_task` and `bluesky-sync` scheduler registration using `BLUESKY_SYNC_ENABLED` and existing bootstrap flow.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add RED tests for scheduled trigger parity and overlap prevention** - `71c01ad` (test)
2. **Task 2: Implement per-source DB lease lock inside run_sync** - `65dfe64` (feat)
3. **Task 3: Wire periodic Bluesky task into scheduler configuration** - `756be99` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `apps/bluesky/tests/test_scheduled_sync.py` - scheduled task contract tests for disabled and enabled paths.
- `apps/bluesky/tests/test_sync_concurrency.py` - overlap skip and lock-release-on-exception tests.
- `apps/bluesky/models.py` - adds sync lease lock fields to source settings.
- `apps/bluesky/migrations/0005_blueskysourcesettings_sync_lock_fields.py` - persists lease lock schema.
- `apps/bluesky/sync.py` - lock acquire/skip/release logic around run_sync pipeline.
- `apps/bluesky/tasks.py` - Celery task wrapper delegating to `run_sync(limit=100)`.
- `taylor_learns/settings.py` - `BLUESKY_SYNC_ENABLED` and `bluesky-sync` periodic schedule entry.

## Decisions Made
- Locking is enforced inside `run_sync`, not only in the task wrapper, so manual command runs are also protected.
- Overlap skip returns existing counters shape with `skipped=1` and no new counter keys.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adjusted test commands for this Django test runner**
- **Found during:** Task 1 and plan verification commands
- **Issue:** Plan-specified `-x` flag is unsupported by `manage.py test` in this repository, causing immediate CLI failure.
- **Fix:** Ran equivalent test commands without `-x` and used `--keepdb` where needed to avoid interactive DB recreation prompt.
- **Files modified:** None
- **Verification:** All task and plan test suites completed successfully with corrected command arguments.
- **Committed in:** N/A (execution-level adjustment only)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope creep; adjustment was execution-only and all acceptance criteria remained satisfied.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SYNC-03 and LIFE-04 behavior are covered with targeted automated tests and scheduler bootstrap verification.
- Phase 04 execution work is complete; ready for phase verification/handoff.

---
*Phase: 04-scheduled-sync-and-concurrency-safety*
*Completed: 2026-03-20*

## Self-Check: PASSED
