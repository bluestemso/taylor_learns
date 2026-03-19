---
phase: 02-deterministic-import-and-auto-publish
plan: 03
subsystem: sync
tags: [bluesky, sync, management-command, idempotency, orchestration]

# Dependency graph
requires:
  - phase: 02-01
    provides: Bluesky source settings and URI-keyed post mapping schema
  - phase: 02-02
    provides: Deterministic publish upsert service and transform contracts
provides:
  - Manual `sync_bluesky` command routed through one deterministic `run_sync` service path
  - listRecords client and reconcile classifier contract for created/updated/skipped operations
  - Idempotent rerun behavior with explicit imported/updated/skipped/failed counters
affects: [phase-03-lifecycle-reconciliation, scheduled-sync, operator-run-visibility]

# Tech tracking
tech-stack:
  added: []
  patterns: [single-sync-entrypoint, operation-classification-before-publish, deterministic-counter-mapping]

key-files:
  created:
    - apps/bluesky/client.py
    - apps/bluesky/reconcile.py
    - apps/bluesky/sync.py
    - apps/bluesky/management/commands/sync_bluesky.py
    - apps/bluesky/tests/test_reconcile.py
    - apps/bluesky/tests/test_sync_bluesky_command.py
  modified:
    - apps/bluesky/tests/test_reconcile.py

key-decisions:
  - "Normalize run_sync counters to imported/updated/skipped/failed while mapping reconcile 'created' to imported."
  - "Keep command thin and delegate all business logic to apps.bluesky.sync.run_sync."
  - "Classify each source record before publish so unchanged CID records are deterministic skips."

patterns-established:
  - "Sync orchestration pattern: select active+enabled source, fetch records, classify, publish only for created/updated."
  - "Operator output pattern: stable key order imported, updated, skipped, failed in command success messages."

requirements-completed: [SYNC-02, SYNC-04]

# Metrics
duration: 7 min
completed: 2026-03-19
---

# Phase 2 Plan 3: Deterministic Import and Auto-Publish Summary

**Manual Bluesky sync now runs through one deterministic orchestration path that imports new posts, safely skips unchanged records on reruns, and reports explicit operation counters.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-19T19:54:33Z
- **Completed:** 2026-03-19T20:02:01Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `list_feed_post_records` and `classify_record_operation` contracts to fetch source records and deterministically label create/update/skip outcomes.
- Added `run_sync(limit=...)` orchestration that selects the active source, classifies each record before publish, and returns deterministic imported/updated/skipped/failed counters.
- Added a thin `sync_bluesky` management command with `--limit` forwarding and stable operator output format.
- Added RED/GREEN test coverage for client/reconcile behavior, orchestration mapping, idempotent reruns, and command wiring.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Bluesky record client and reconcile decision logic (RED)** - `a0f2d43` (test)
2. **Task 1: Implement Bluesky record client and reconcile decision logic (GREEN)** - `f0d6788` (feat)
3. **Task 2: Implement run_sync orchestration and manual sync_bluesky command (RED)** - `416639c` (test)
4. **Task 2: Implement run_sync orchestration and manual sync_bluesky command (GREEN)** - `62160dc` (feat)

## Files Created/Modified
- `apps/bluesky/client.py` - listRecords HTTP client for `app.bsky.feed.post` with normalized payload shape.
- `apps/bluesky/reconcile.py` - deterministic `created`/`updated`/`skipped` classifier based on existing URI map and CID comparison.
- `apps/bluesky/sync.py` - single orchestration path for source selection, per-record classification, publish gating, and counter mapping.
- `apps/bluesky/management/commands/sync_bluesky.py` - manual command entrypoint forwarding `--limit` and printing deterministic counters.
- `apps/bluesky/tests/test_reconcile.py` - client call contract and classification tests.
- `apps/bluesky/tests/test_sync_bluesky_command.py` - orchestration and command wiring contract tests including idempotent rerun behavior.

## Decisions Made
- Standardized on reconcile operation values (`created`, `updated`, `skipped`) and explicitly mapped `created -> imported` in sync counters for operator clarity.
- Kept `sync_bluesky` command intentionally thin so all sync behavior remains testable and reusable from `run_sync`.
- Preserved safe rerun behavior by classifying every source URI/CID pair before deciding whether publish mutations are allowed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 2 deterministic import wiring is complete; manual sync now has a stable orchestration base ready for Phase 3 lifecycle reconciliation and run visibility enhancements.

## Self-Check: PASSED

- Verified key files exist on disk.
- Verified all task commit hashes exist in git history.

---
*Phase: 02-deterministic-import-and-auto-publish*
*Completed: 2026-03-19*
