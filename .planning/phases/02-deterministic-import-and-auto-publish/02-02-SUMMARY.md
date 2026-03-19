---
phase: 02-deterministic-import-and-auto-publish
plan: 02
subsystem: publishing
tags: [bluesky, wagtail, micropost, facets, utf8, dedupe]

# Dependency graph
requires:
  - phase: 02-01
    provides: Bluesky source and post mapping models used by publish upsert service
provides:
  - Facet-aware Bluesky text-to-HTML rendering for MicroPost body paragraphs
  - Deterministic create/update/skip micropost publish service keyed by source URI and CID
  - Contract tests for transform fidelity and auto-publish dedupe behavior
affects: [phase-02-plan-03, bluesky-sync-orchestration, import-fidelity]

# Tech tracking
tech-stack:
  added: []
  patterns: [utf8-byte-facet-slicing, uri-cid-upsert, wagtail-save-revision-publish]

key-files:
  created:
    - apps/bluesky/transform.py
    - apps/bluesky/publish.py
    - apps/bluesky/tests/test_transform.py
    - apps/bluesky/tests/test_publish.py
  modified: []

key-decisions:
  - "Use Bluesky facet byteStart/byteEnd offsets over UTF-8 bytes and render only canonical link facets."
  - "Select the first live BlogIndexPage ordered by id as deterministic micropost import parent."
  - "Treat unchanged source_cid for existing source_uri as a no-op skip to prevent duplicate writes."

patterns-established:
  - "Facet parsing pattern: filter features to app.bsky.richtext.facet#link and escape non-link text segments."
  - "Publish mutation pattern: save model changes and call save_revision().publish() for live content."

requirements-completed: [PUBL-01, PUBL-02, PUBL-03]

# Metrics
duration: 7 min
completed: 2026-03-19
---

# Phase 2 Plan 2: Deterministic Import and Auto-Publish Summary

**Facet-aware Bluesky text rendering and deterministic micropost upsert publishing now preserve canonical links and keep imported entries live without duplicate page creation.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-19T19:41:21Z
- **Completed:** 2026-03-19T19:49:11Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Implemented `render_post_body_html` and `build_micropost_stream_body` with UTF-8 byte-aware facet handling for canonical link rendering.
- Implemented `upsert_and_publish_micro_post` with deterministic parent selection, create/update/skip behavior, and Wagtail revision publish calls.
- Added contract tests validating text/link fidelity, UTF-8 boundaries, dedupe behavior, and live publish outcomes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build facet-aware text and link transformation service (RED)** - `4ae0b52` (test)
2. **Task 1: Build facet-aware text and link transformation service (GREEN)** - `9e7cd9e` (feat)
3. **Task 2: Implement deterministic micro post upsert and auto-publish service (RED)** - `6d2b614` (test)
4. **Task 2: Implement deterministic micro post upsert and auto-publish service (GREEN)** - `84d2538` (feat)

## Files Created/Modified
- `apps/bluesky/transform.py` - Facet-aware UTF-8 byte offset HTML rendering and StreamField paragraph wrapper.
- `apps/bluesky/publish.py` - Deterministic micropost create/update/skip upsert service with auto-publish.
- `apps/bluesky/tests/test_transform.py` - Contract tests for text/link transform behavior.
- `apps/bluesky/tests/test_publish.py` - Integration-style contract tests for publish lifecycle and dedupe.

## Decisions Made
- Used facet metadata (`app.bsky.richtext.facet#link`) as the only in-scope link source to preserve canonical URIs.
- Enforced deterministic parent page selection via `BlogIndexPage.objects.live().order_by("id").first()` with explicit failure when none exists.
- Returned `skipped` when `source_uri` exists and `source_cid` is unchanged to keep reruns idempotent.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-02 outputs are complete and verified; phase is ready for plan 02-03 orchestration wiring.

## Self-Check: PASSED

- Verified key files exist on disk.
- Verified all task commit hashes exist in git history.

---
*Phase: 02-deterministic-import-and-auto-publish*
*Completed: 2026-03-19*
