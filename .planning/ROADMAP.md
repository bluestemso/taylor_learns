# Roadmap: Taylor Learns

## Overview

This milestone delivers a reliable one-way mirror from Taylor's Bluesky account into the site's microblog stream, starting with source binding and safe import boundaries, then adding deterministic publish behavior, lifecycle reconciliation, and finally automated scheduling with concurrency safety.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Source Setup and Import Scope** - Bind the single owner source and define controlled historical import boundaries. (completed 2026-03-19)
- [ ] **Phase 2: Deterministic Import and Auto-Publish** - Import new posts safely, deduplicate by source identity, and publish text/link content automatically.
- [ ] **Phase 3: Post Lifecycle Reconciliation and Run Visibility** - Keep mirrored entries aligned with Bluesky edits/deletes and expose sync outcomes.
- [ ] **Phase 4: Scheduled Sync and Concurrency Safety** - Automate recurring sync with overlap prevention for reliable operations.

## Phase Details

### Phase 1: Source Setup and Import Scope
**Goal**: User can configure the single authorized Bluesky source and limit initial import history to a chosen window.
**Depends on**: Nothing (first phase)
**Requirements**: SYNC-01, SYNC-05
**Success Criteria** (what must be TRUE):
  1. User can connect exactly one owner Bluesky account as the active import source.
  2. User can configure a backfill window before first import to limit historical post ingestion.
  3. User can view the currently configured source and backfill settings used by sync runs.
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Create `apps/bluesky` source-settings contract (model, identity verification service, and contract tests).
- [ ] 01-03-PLAN.md — Register the new app and add initial schema migration for single-source + backfill constraints.
- [ ] 01-02-PLAN.md — Implement guided Django admin setup flow with replace confirmation and effective settings visibility.

### Phase 2: Deterministic Import and Auto-Publish
**Goal**: User can run safe, repeatable imports that create published microblog entries with accurate text/link content and no duplicates.
**Depends on**: Phase 1
**Requirements**: SYNC-02, SYNC-04, PUBL-01, PUBL-02, PUBL-03
**Success Criteria** (what must be TRUE):
  1. User can run a manual sync that imports new Bluesky posts into site microblog entries.
  2. Re-running sync does not create duplicate entries for already-imported source posts.
  3. Imported entries display Bluesky text content accurately.
  4. Imported entries preserve Bluesky links in the rendered microblog content.
  5. Newly imported entries are auto-published without manual review.
**Plans**: TBD

### Phase 3: Post Lifecycle Reconciliation and Run Visibility
**Goal**: User can trust the mirrored microblog feed to stay aligned with Bluesky post changes and can inspect what each sync run did.
**Depends on**: Phase 2
**Requirements**: LIFE-01, LIFE-02, LIFE-03
**Success Criteria** (what must be TRUE):
  1. When a Bluesky post is edited, the corresponding microblog entry reflects that edit after sync.
  2. When a Bluesky post is deleted, the corresponding microblog entry is soft-removed after sync.
  3. User can view sync run results with counts for imported, updated, removed, and skipped posts.
**Plans**: TBD

### Phase 4: Scheduled Sync and Concurrency Safety
**Goal**: User can rely on automated sync cadence without overlapping runs corrupting or duplicating lifecycle outcomes.
**Depends on**: Phase 3
**Requirements**: SYNC-03, LIFE-04
**Success Criteria** (what must be TRUE):
  1. User can enable recurring scheduled sync runs that execute without manual intervention.
  2. If a sync is already in progress for the source, a second run is prevented from overlapping.
  3. Scheduled sync behavior produces the same safe import/update/remove outcomes as manual sync.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Source Setup and Import Scope | 3/3 | Complete   | 2026-03-19 |
| 2. Deterministic Import and Auto-Publish | 0/TBD | Not started | - |
| 3. Post Lifecycle Reconciliation and Run Visibility | 0/TBD | Not started | - |
| 4. Scheduled Sync and Concurrency Safety | 0/TBD | Not started | - |
