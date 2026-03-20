# Taylor Learns

## What This Is

Taylor Learns is Taylor Schaack's personal blog and portfolio site. It combines long-form CMS content, small utilities, and app-specific experiences in a single Django/Wagtail application. This milestone adds a publishing bridge so Bluesky activity can flow into the site's microblog stream.

## Core Value

Publish in one place and reliably syndicate personal writing/activity so the site remains the canonical home for content.

## Current Milestone: v1.0 Bluesky Microblog Import

**Goal:** Automatically mirror Taylor's Bluesky posts into site microblog entries with safe, repeatable sync behavior.

**Target features:**
- Monitor only Taylor's Bluesky account as the import source.
- Support both manual sync runs and scheduled sync runs.
- Auto-publish imported microblog entries from Bluesky content.
- Sync post edits and soft-delete entries when source posts are removed.
- Scope v1 content to text and links only.

## Requirements

### Validated

- ✓ Site serves CMS-managed content via Django + Wagtail in `apps/content/` and `templates/` — existing
- ✓ Background job infrastructure exists with Celery/Redis in `taylor_learns/celery.py` and `taylor_learns/settings.py` — existing
- ✓ External content sync patterns already exist via gadgets pipeline in `apps/gadgets/sync.py` and `apps/gadgets/tasks.py` — existing
- ✓ Bluesky account sync can fetch posts for the site owner and import them into microblog content. — Validated in Phase 2: Deterministic Import and Auto-Publish
- ✓ Imported posts are auto-published and deduplicated by source post ID. — Validated in Phase 2: Deterministic Import and Auto-Publish
- ✓ Sync can run manually and on schedule using existing job infrastructure. — Validated in Phase 4: Scheduled Sync and Concurrency Safety

### Active

- [x] Edit and delete events from Bluesky update or soft-remove corresponding microblog entries.

## Current State

Phase 4 is complete: scheduled sync and per-source overlap protection are implemented and verified.
Milestone v1.0 execution is complete across all planned phases.

### Out of Scope

- Multi-account monitoring — not required for this milestone.
- Bluesky firehose/realtime ingestion — deferred; polling/manual sync is sufficient for v1.
- Rich media import (images/video) — deferred for a later milestone.
- Relationship graph import (reply threading and quote-post references) — deferred for a later milestone.

## Context

- Existing stack already supports server-rendered content workflows and background processing.
- Sync-style operational precedent exists in gadget repository ingestion and scheduled tasks.
- The new integration should align with current Django app boundaries and avoid introducing a new service unless necessary.
- This milestone focuses on dependable content mirroring over advanced social features.

## Constraints

- **Tech stack**: Must integrate into existing Django/Wagtail/Celery architecture — avoids unnecessary platform complexity.
- **Data reliability**: Must prevent duplicate imports and handle upstream edits/deletes deterministically — protects content integrity.
- **Operational scope**: Start with owner-account only and polling/manual sync — reduces risk while validating value.
- **Publishing workflow**: Auto-publish behavior is required for this milestone — keeps site feed current without moderation overhead.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Start with owner account only | Narrow scope, validate end-to-end pipeline first | — Pending |
| Use manual + scheduled sync | Balances control with automation and fits existing Celery model | — Pending |
| Auto-publish imported entries | User preference for low-friction publishing | — Pending |
| v1 content limited to text and links | Minimize integration complexity for first release | — Pending |
| Sync edits and soft-delete removals | Keep mirrored feed aligned with source without hard data loss | Implemented in Phase 3 |
| Treat Bluesky lifecycle edits as delete+repost in live verification | Bluesky does not support true post editing semantics | Accepted during Phase 3 human verification |

---
*Last updated: 2026-03-20 after Phase 4 execution completion*
