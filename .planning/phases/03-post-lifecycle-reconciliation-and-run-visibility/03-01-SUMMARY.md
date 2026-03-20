---
phase: 03-post-lifecycle-reconciliation-and-run-visibility
plan: 01
subsystem: sync
tags: [bluesky, lifecycle, reconciliation, pagination, wagtail]

# Dependency graph
requires:
  - phase: 02-03
    provides: Deterministic run_sync orchestration, operation classification, and URI/CID map contracts
provides:
  - Lifecycle reconciliation coverage for edited and deleted Bluesky source posts
  - Soft-remove workflow that unpublishes mapped micro posts and records one-time removal state
  - Two-pass sync behavior that exhausts listRecords pagination before missing-URI removal reconciliation
affects: [phase-03-plan-02-run-visibility, phase-04-scheduled-sync, operator-observability]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-pass-reconciliation, soft-remove-with-removed-at, cursor-exhaustion-before-delete-pass]

key-files:
  created:
    - apps/bluesky/tests/test_sync_lifecycle_reconciliation.py
    - apps/bluesky/migrations/0003_blueskypostmap_removed_at.py
  modified:
    - apps/bluesky/tests/test_reconcile.py
    - apps/bluesky/models.py
    - apps/bluesky/reconcile.py
    - apps/bluesky/publish.py
    - apps/bluesky/sync.py
    - apps/bluesky/tests/test_sync_bluesky_command.py

key-decisions:
  - "Track soft-deleted source posts with BlueskyPostMap.removed_at and exclude them from repeat removal reconciliation."
  - "Perform lifecycle sync in two passes: fetch/classify all remote records first, then compute missing mapped URIs for remove operations."
  - "Cap listRecords page size at 100 and follow cursors until exhausted so deletion detection uses complete remote URI state."

patterns-established:
  - "Lifecycle parity pattern: update on CID change, unpublish on missing URI, no repeated remove increments while source remains absent."
  - "Counter contract pattern: run_sync always returns imported, updated, removed, skipped, failed keys."

requirements-completed: [LIFE-01, LIFE-02]

# Metrics
duration: 6 min
completed: 2026-03-20
---

# Phase 3 Plan 1: Post Lifecycle Reconciliation and Run Visibility Summary

**Bluesky lifecycle sync now reconciles edited and deleted source posts by updating mapped micro content on CID changes and soft-unpublishing missing mapped URIs with one-time remove accounting.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T16:00:53Z
- **Completed:** 2026-03-20T16:06:48Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Added RED lifecycle tests for edit reconciliation and delete reconciliation (including one-time remove counting behavior).
- Added `removed_at` lifecycle state, plus publish/reconcile helpers for deterministic soft-remove operations.
- Extended `run_sync` to two-pass processing: full cursor pagination for remote state, then missing-URI removal reconciliation.
- Updated sync contract tests to validate removed counter presence and cursor pagination exhaustion.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create failing lifecycle reconciliation tests for edits and removals** - `97c436e` (test)
2. **Task 2: Implement removal state contracts and soft-remove publish operation** - `80b0158` (feat)
3. **Task 3: Wire two-pass run_sync reconciliation with removed counter** - `2c372bd` (feat)

## Files Created/Modified

- `apps/bluesky/tests/test_sync_lifecycle_reconciliation.py` - Contract tests for edit updates, soft-remove, and one-time removal counting.
- `apps/bluesky/tests/test_reconcile.py` - Helper-level tests for missing URI candidate selection excluding already removed rows.
- `apps/bluesky/models.py` - Added nullable `removed_at` lifecycle marker to `BlueskyPostMap`.
- `apps/bluesky/migrations/0003_blueskypostmap_removed_at.py` - Migration for persisted removal metadata.
- `apps/bluesky/reconcile.py` - Added missing mapped URI helper for deletion candidate detection.
- `apps/bluesky/publish.py` - Added `unpublish_mapped_micro_post` soft-remove operation and reset `removed_at` on updates.
- `apps/bluesky/sync.py` - Added removed counter and two-pass orchestration with cursor exhaustion.
- `apps/bluesky/tests/test_sync_bluesky_command.py` - Added run_sync pagination/counter contract assertions.

## Decisions Made

- Used `removed_at` as the lifecycle source of truth so removals are idempotent across repeated sync runs.
- Kept soft-remove behavior in the publish layer via Wagtail `unpublish` to preserve history while removing from live feed.
- Required full remote pagination before delete reconciliation to avoid false missing-URI removals from partial pages.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added interim removed counter wiring during Task 2 verification**
- **Found during:** Task 2 (model/publish/reconcile implementation)
- **Issue:** Task 2 verification suite included lifecycle tests requiring `removed` key in `run_sync` output, which blocked green verification before Task 3 orchestration work.
- **Fix:** Added removed counter key and remove-pass hook in `run_sync` while still completing full pagination orchestration in Task 3.
- **Files modified:** `apps/bluesky/sync.py`
- **Verification:** `make test ARGS='apps.bluesky.tests.test_sync_lifecycle_reconciliation apps.bluesky.tests.test_publish apps.bluesky.tests.test_reconcile'`
- **Committed in:** `80b0158` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Deviation was required to satisfy task verification ordering; no architectural scope changes.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Lifecycle parity for update/remove behavior is now deterministic and test-covered. Phase 3 Plan 2 can build run-result persistence and operator-facing visibility on top of the stabilized counter contract.

## Self-Check: PASSED

- Verified summary and key implementation files exist on disk.
- Verified task commit hashes (`97c436e`, `80b0158`, `2c372bd`) exist in git history.
