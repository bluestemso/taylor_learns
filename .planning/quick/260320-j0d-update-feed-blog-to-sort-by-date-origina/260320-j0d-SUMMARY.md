---
phase: quick-260320-j0d-update-feed-blog-to-sort-by-date-origina
plan: 01
subsystem: api
tags: [bluesky, wagtail, feed-ordering, regression-tests]
requires: []
provides:
  - Blog/feed entries now sort by content date with deterministic fallback behavior
  - Bluesky sync timestamp selection now prefers original createdAt values
  - Regression coverage for feed ordering and sync timestamp contracts
affects: [content-feed, bluesky-import]
tech-stack:
  added: []
  patterns:
    - TDD regression-first coverage for ordering and timestamp contracts
key-files:
  created:
    - apps/content/tests/__init__.py
    - apps/content/tests/test_blog_index_ordering.py
  modified:
    - apps/bluesky/tests/test_sync_bluesky_command.py
    - apps/bluesky/sync.py
    - apps/content/models.py
key-decisions:
  - "Order BlogIndex descendants in Python using page date first, then publish timestamp/id fallback for no-date pages."
  - "Prefer Bluesky value.createdAt over indexedAt to preserve original posted chronology during backfills."
patterns-established:
  - "Use explicit sync contract tests to lock timestamp precedence behavior."
requirements-completed: [QUICK-260320-J0D]
duration: 5m
completed: 2026-03-20
---

# Phase quick-260320-j0d Plan 01: Update feed blog to sort by date summary

**Blog feed chronology now follows each post's own date while Bluesky imports preserve original created timestamps for stable backfill ordering.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T18:44:41Z
- **Completed:** 2026-03-20T18:49:26Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added regression tests that capture date-first blog ordering and Bluesky timestamp precedence/fallback behavior.
- Updated Bluesky sync to prioritize `value.createdAt` while retaining `indexedAt` fallback compatibility.
- Replaced publish-time feed ordering with deterministic content-date ordering plus no-date fallback handling.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add regression tests for feed ordering and timestamp preference** - `ada387c` (test)
2. **Task 2: Implement original-posted timestamp mapping in Bluesky sync/publish path** - `da0e90d` (feat)
3. **Task 3: Switch BlogIndex ordering from publish timestamp to content date** - `8df0012` (test), `083bcc2` (feat)

## Files Created/Modified

- `apps/content/tests/__init__.py` - Enables content app test package discovery.
- `apps/content/tests/test_blog_index_ordering.py` - Regression tests for date-first ordering and no-date fallback behavior.
- `apps/bluesky/tests/test_sync_bluesky_command.py` - Sync contract tests for createdAt precedence and indexedAt fallback.
- `apps/bluesky/sync.py` - Timestamp extraction now prefers original Bluesky post creation time.
- `apps/content/models.py` - Blog index ordering now uses content date with deterministic fallback keys.

## Decisions Made

- Ordered `BlogIndexPage` children using a date-first key and deterministic fallback tuple to support polymorphic descendants.
- Kept `upsert_and_publish_micro_post` contract unchanged and fixed behavior at sync extraction to minimize surface-area changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced unsupported test flag in verification commands**
- **Found during:** Task 1 verification
- **Issue:** `make test ARGS='... -x --keepdb'` fails because this Django test runner does not support `-x`.
- **Fix:** Executed verification commands with `--keepdb` and explicit test labels, omitting `-x`.
- **Files modified:** None
- **Verification:** Targeted test suites executed successfully with equivalent scope.
- **Committed in:** N/A (execution-only adjustment)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope change; deviation only adjusted test command flags to match project tooling.

## Issues Encountered

- None beyond the unsupported `-x` flag compatibility issue.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Feed ordering and Bluesky backfill chronology are now covered by regression tests and implementation updates.
- Ready for manual visual verification in `/blog/` if desired.

## Self-Check: PASSED

- FOUND: `.planning/quick/260320-j0d-update-feed-blog-to-sort-by-date-origina/260320-j0d-SUMMARY.md`
- FOUND commits: `ada387c`, `da0e90d`, `8df0012`, `083bcc2`
