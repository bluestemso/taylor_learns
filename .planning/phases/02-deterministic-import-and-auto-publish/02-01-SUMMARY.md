---
phase: 02-deterministic-import-and-auto-publish
plan: 01
subsystem: database
tags: [django, wagtail, bluesky, migrations, deduplication]

# Dependency graph
requires:
  - phase: 01-source-setup-and-import-scope
    provides: Active Bluesky source settings with verified DID for import scope
provides:
  - Deterministic Bluesky source-post mapping model keyed by source URI
  - Database-level uniqueness guard for imported source post identity
  - Contract tests proving required mapping fields and source relationships
affects: [02-02-PLAN, 02-03-PLAN, phase-03-lifecycle-reconciliation]

# Tech tracking
tech-stack:
  added: []
  patterns: [URI-keyed source mapping, DB-enforced dedupe constraints]

key-files:
  created:
    - apps/bluesky/migrations/0002_blueskypostmap.py
  modified:
    - apps/bluesky/models.py
    - apps/bluesky/tests/test_post_map_model.py

key-decisions:
  - "Use dedicated BlueskyPostMap model instead of heuristic matching fields on MicroPostPage."
  - "Enforce source_uri uniqueness at model and migration constraint layers for idempotent reruns."

patterns-established:
  - "Deterministic import identity: persist Bluesky record URI and source metadata on a separate map table."
  - "Contract-first import foundations: validate schema behavior with dedicated model contract tests before sync orchestration."

requirements-completed: [SYNC-04]

# Metrics
duration: 2 min
completed: 2026-03-19
---

# Phase 2 Plan 01: Deterministic Mapping Contract Summary

**Bluesky source records now persist in a dedicated URI-keyed map model that enforces dedupe safety for idempotent sync reruns.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-19T19:36:38Z
- **Completed:** 2026-03-19T19:38:17Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments
- Added `BlueskyPostMap` in `apps/bluesky/models.py` with required source identity fields, source settings link, and micro post link.
- Added migration `apps/bluesky/migrations/0002_blueskypostmap.py` including explicit `unique_bluesky_post_map_source_uri` constraint.
- Added contract tests in `apps/bluesky/tests/test_post_map_model.py` validating uniqueness enforcement, required fields, and linkage contracts.

## Task Commits

Each task was committed atomically:

1. **Task 1 (TDD RED): Add contract tests for deterministic post map** - `3ff791b` (test)
2. **Task 1 (TDD GREEN): Implement deterministic Bluesky post map schema** - `1d20067` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `apps/bluesky/models.py` - Added `BlueskyPostMap` model contract and uniqueness constraints.
- `apps/bluesky/migrations/0002_blueskypostmap.py` - Created schema migration for post map table and uniqueness constraint.
- `apps/bluesky/tests/test_post_map_model.py` - Added deterministic mapping contract tests.

## Decisions Made
- Use a dedicated mapping table (`BlueskyPostMap`) to preserve stable Bluesky source identity separate from content rendering concerns.
- Make `source_uri` globally unique and constrained in schema so reruns are deterministic and collision-safe.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for `02-02-PLAN.md` to implement facet-aware transform and auto-publish upsert behavior on top of deterministic identity mapping.
- No blockers carried forward.

## Self-Check: PASSED

- Verified summary file and key migration file exist on disk.
- Verified task commits `3ff791b` and `1d20067` exist in git history.
