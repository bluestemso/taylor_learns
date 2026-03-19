# Architecture Research

**Domain:** Bluesky-to-CMS microblog import (manual + scheduled sync with reconciliation)
**Researched:** 2026-03-19
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Trigger Layer (existing)                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Django Admin action   Management command   Celery beat periodic task      │
│         │                     │                       │                      │
└─────────┴─────────────────────┴───────────────────────┴──────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│ Bluesky Sync App (new: apps/bluesky/)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  client.py      sync.py        reconcile.py      publish.py      tasks.py   │
│ (XRPC calls) (run orches.)   (diff engine)   (Wagtail writes) (async entry)│
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│ Persistence Layer (modified + new)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  New: BlueskySource + BlueskyPostMap models (source-of-truth metadata)     │
│  Existing: Wagtail MicroPostPage under BlogIndexPage (published content)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### New vs Modified Components

| Area | Type | Responsibility | Notes |
|------|------|----------------|-------|
| `apps/bluesky/models.py` | **New** | Store source account config, last sync cursor/state, and per-post source mapping (`at_uri`, `cid`, `rkey`, deletion state) | Keep source metadata out of `apps/content/models.py` |
| `apps/bluesky/client.py` | **New** | Bluesky/ATProto HTTP integration (`com.atproto.repo.listRecords`, optional `com.atproto.identity.resolveHandle`) | Use `httpx` pattern already used in `apps/gadgets/sync.py` |
| `apps/bluesky/sync.py` | **New** | Orchestrate full run and status transitions | Mirror `apps/gadgets/sync.py` run-summary style |
| `apps/bluesky/reconcile.py` | **New** | Compute create/update/soft-delete sets from source snapshot vs local map | Deterministic idempotent reconciliation core |
| `apps/bluesky/publish.py` | **New** | Apply creates/updates/unpublishes to `MicroPostPage` and mapping table | Owns Wagtail page mutation boundaries |
| `apps/bluesky/tasks.py` | **New** | Celery entrypoint for scheduled sync | Gate with `BLUESKY_SYNC_ENABLED` setting |
| `apps/bluesky/management/commands/sync_bluesky.py` | **New** | Manual CLI sync trigger | Keep parity with `sync_gadgets.py` UX |
| `apps/bluesky/admin.py` | **New** | Manual admin trigger + status visibility | Keep operator workflow in Django admin |
| `taylor_learns/settings.py` | **Modified** | Add Bluesky env vars + add schedule to `SCHEDULED_TASKS` | Reuse existing `bootstrap_celery_tasks` flow |
| `apps/web/management/commands/bootstrap_celery_tasks.py` | **Reused (no code change likely)** | Creates/updates periodic task rows from `SCHEDULED_TASKS` | Bluesky task auto-bootstraps with settings entry |
| `apps/content/models.py` | **Unchanged preferred** | Continue owning rendered microblog pages | Avoid coupling import metadata into Wagtail page schema |

## Recommended Project Structure

```text
apps/
└── bluesky/
    ├── __init__.py
    ├── admin.py                  # Source config + "sync now" actions
    ├── apps.py
    ├── client.py                 # XRPC client wrappers, auth, pagination
    ├── models.py                 # BlueskySource, BlueskyPostMap, SyncStatus
    ├── sync.py                   # run_sync(), summaries, error boundaries
    ├── reconcile.py              # diff(source_records, local_records)
    ├── publish.py                # create/update/unpublish MicroPostPage
    ├── tasks.py                  # sync_bluesky_task
    ├── management/
    │   └── commands/
    │       └── sync_bluesky.py
    ├── migrations/
    └── tests/
        ├── test_reconcile.py
        ├── test_sync_command.py
        └── test_publish.py
```

### Structure Rationale

- `apps/bluesky/` isolates external-source import concerns from CMS page definitions.
- `reconcile.py` and `publish.py` split "decision" from "mutation," making retries safe and tests focused.
- Mapping models in the import app preserve clean ownership: source identity and sync state stay outside Wagtail page schema.

## Architectural Patterns

### Pattern 1: Snapshot Reconciliation (source-first)

**What:** Each run pulls a source snapshot (all target `app.bsky.feed.post` records for owner repo) and reconciles local state against it.
**When to use:** Manual runs, scheduled runs, and recovery after downtime.
**Trade-offs:** More API reads per run, but deterministic delete detection and simpler correctness than incremental-only polling.

**Example:**
```python
source_records = client.list_all_posts(repo=source.did, collection='app.bsky.feed.post')
plan = reconcile(source_records=source_records, local_mappings=BlueskyPostMap.objects.for_source(source))
publish.apply(plan)
```

### Pattern 2: Idempotent Upsert + Soft Delete

**What:** Upsert by stable source key (`at_uri` or `(repo_did, rkey)`), update when `cid` changes, soft-delete when missing from source snapshot.
**When to use:** Any recurring ingestion where edits/deletes must mirror upstream.
**Trade-offs:** Requires mapping table and status tracking, but prevents duplicates and supports exact reconciliation.

### Pattern 3: Trigger/Worker Separation

**What:** Admin/CLI/beat only trigger; all sync logic lives in `sync.py` service called by both sync and async paths.
**When to use:** Multiple entry points for same domain workflow.
**Trade-offs:** Slight indirection, but one execution path means less drift and easier testing.

## Data Flow

### Manual Sync Flow

```text
[Admin "Sync now" or manage.py sync_bluesky]
    ↓
[apps/bluesky/sync.run_sync]
    ↓
[client.listRecords pagination on app.bsky.feed.post]
    ↓
[reconcile.diff against BlueskyPostMap]
    ↓
[publish.apply -> create/update/unpublish MicroPostPage]
    ↓
[persist sync summary/status timestamps]
```

### Scheduled Sync Flow

```text
[Celery beat -> PeriodicTask]
    ↓
[apps/bluesky/tasks.sync_bluesky_task]
    ↓
[apps/bluesky/sync.run_sync] (same path as manual)
```

### Ownership Boundaries

| Boundary | Owner | Contract |
|----------|-------|----------|
| Bluesky API semantics (pagination, auth, rate-limit backoff) | `apps/bluesky/client.py` | Returns normalized source records; never mutates CMS |
| Reconciliation decisions (create/update/delete/skip) | `apps/bluesky/reconcile.py` | Pure decision layer from source + local map |
| CMS mutation and publish state | `apps/bluesky/publish.py` + `apps/content` models | Applies plan atomically per record; no API calls |
| Scheduling and runtime triggering | Celery/task + admin/command | Invoke `run_sync`; no business logic duplication |

### Reconciliation Rules (recommended)

1. Resolve configured handle to DID once per run (cache DID on source model).
2. Fetch full post collection snapshot via `com.atproto.repo.listRecords` (`collection=app.bsky.feed.post`, cursor paging).
3. Filter to v1-supported records (text + link facets only).
4. For each source record:
   - create mapping + `MicroPostPage` if unseen
   - update page if `cid` changed (source edit)
   - no-op if unchanged
5. For local mappings missing from snapshot:
   - mark mapping soft-deleted with timestamp
   - unpublish corresponding Wagtail page (retain record for audit/recovery)

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Bluesky PDS / AppView (`com.atproto.*`, `app.bsky.*`) | HTTP XRPC client with token auth where needed | Prefer repo reads for reconciliation completeness; respect 429 backoff |
| Redis + Celery beat (existing) | Existing scheduler/worker topology | Add Bluesky task to `SCHEDULED_TASKS` and bootstrap |

### Internal Integration Points

| Module Boundary | Communication | Notes |
|-----------------|---------------|-------|
| `apps/bluesky` ↔ `apps/content` | Direct ORM/Wagtail model calls | `apps/content` remains rendering domain; bluesky app owns import metadata |
| `apps/bluesky/tasks.py` ↔ `apps/bluesky/sync.py` | Function call | Same orchestration path for manual and scheduled runs |
| `taylor_learns/settings.py` ↔ `apps/web/.../bootstrap_celery_tasks.py` | Settings contract (`SCHEDULED_TASKS`) | Keep deployment workflow unchanged |

## Suggested Build Order (dependency-aware)

1. **Source state models + migrations**
   - Add `BlueskySource` and `BlueskyPostMap` with unique constraints on source identity (`at_uri` or DID+rkey).
   - Dependency: none; unlocks all later work.

2. **Bluesky client + normalization layer**
   - Implement `listRecords` pagination and source-record normalization.
   - Dependency: source models for persisted source config and sync state.

3. **Reconciliation engine (pure diff)**
   - Implement create/update/delete plan generation with tests.
   - Dependency: normalized source payload shape + mapping model schema.

4. **Publisher (Wagtail mutation path)**
   - Implement create/update/unpublish behavior for `MicroPostPage` and mapping updates.
   - Dependency: reconciliation output contract.

5. **Sync orchestrator + entry points**
   - Wire `run_sync` + management command + admin "sync now".
   - Dependency: client, reconcile, publish complete.

6. **Scheduled execution integration**
   - Add task + settings schedule + bootstrap integration.
   - Dependency: orchestrator complete.

7. **Operational hardening**
   - Add rate-limit/backoff behavior, observability fields, and failure-mode tests.
   - Dependency: end-to-end path present.

## Sources

- Bluesky API hosts/auth patterns: https://docs.bsky.app/docs/advanced-guides/api-directory
- Bluesky repo record APIs (`listRecords`, `getRecord`): https://docs.bsky.app/docs/api/com-atproto-repo-list-records and https://docs.bsky.app/docs/api/com-atproto-repo-get-record
- Bluesky author feed semantics (for optional feed-view reads): https://docs.bsky.app/docs/api/app-bsky-feed-get-author-feed
- AT URI durability caveats (handle vs DID): https://atproto.com/specs/at-uri-scheme
- Bluesky rate limits and 429 behavior guidance: https://docs.bsky.app/docs/advanced-guides/rate-limits
- Identity resolution recommendations (handle->DID, caching): https://docs.bsky.app/docs/advanced-guides/resolving-identities
- Wagtail Page model/publish semantics: https://docs.wagtail.org/en/stable/reference/models.html
- django-celery-beat scheduling model: https://django-celery-beat.readthedocs.io/en/latest/

---
*Architecture research for: Bluesky-to-CMS microblog import integration*
*Researched: 2026-03-19*
