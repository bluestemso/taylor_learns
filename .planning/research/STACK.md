# Stack Research

**Domain:** Bluesky-to-CMS microblog ingestion (existing Django/Wagtail app)
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Django + Wagtail (existing) | Django 5.2.x / Wagtail 7.2.x | Persist imported posts as first-class CMS microblog entries | This is already the system of record, so importing directly into Wagtail `MicroPostPage` avoids dual-write complexity and keeps editorial tooling unchanged. |
| Celery workers + Redis (existing) | Celery 5.x + Redis 7.x (repo-managed) | Run manual and scheduled sync jobs safely off-request | Existing infra already supports background sync patterns (`apps/gadgets/*`), retries, and operational visibility. Reusing it avoids introducing another job runtime. |
| Bluesky XRPC HTTP APIs via `httpx` (existing) | `httpx>=0.28.1` (already in `pyproject.toml`) | Pull canonical Bluesky records and map them to CMS entries | `httpx` is already your integration client standard (GitHub sync, weather tools). Reusing it keeps networking behavior and timeout handling consistent. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `django-celery-beat` (existing) | 2.9.0 current release (PyPI, 2026-02-28) | DB-backed schedule for recurring Bluesky sync | Use for scheduled sync cadence (hourly/15-min) and enable/disable in admin without redeploying code. |
| `atproto` (optional, NOT default for v1) | 0.0.65 (PyPI, 2025-12-08) | Typed SDK for AT Protocol if raw XRPC maintenance becomes painful | Only adopt if raw endpoint/model handling grows too complex. For v1, avoid due pre-1.0 API churn warning from project docs. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Django management command (`sync_bluesky`) | Manual/on-demand sync trigger | Mirror existing `sync_gadgets` command shape for operator familiarity and testability. |
| Django admin action/button | Manual sync from admin UI | Mirror existing gadgets admin `sync-now` pattern for non-CLI execution. |

## Installation

```bash
# No new dependency required for v1 (recommended path):
# reuse existing httpx + celery + django-celery-beat stack

# Optional only (if later choosing typed AT Protocol SDK):
make uv add 'atproto==0.0.65'
make requirements
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Raw XRPC calls with existing `httpx` | `atproto` Python SDK | Use SDK if team prioritizes generated typed models over minimizing dependencies and accepts pre-1.0 churn risk. |
| Polling via Celery schedule/manual runs | Firehose (`com.atproto.sync.subscribeRepos`) realtime ingest | Use firehose only when near-realtime propagation is required and ops budget allows websocket consumers, checkpointing, and replay handling. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Firehose ingestion in v1 | Over-scoped for owner-account import; adds stateful stream processing and recovery complexity not needed for milestone goals | Scheduled polling with Celery + manual sync trigger |
| New queue/scheduler platform (RQ, Dramatiq, cron sidecar, external workflow engine) | Duplicates existing Celery + beat capability and increases operational surface area | Existing Celery workers + `django-celery-beat` |
| Full ATProto SDK as mandatory base in v1 | Current SDK explicitly warns pre-1.0 compatibility is not guaranteed; creates upgrade volatility for a small integration | Direct `httpx` calls to stable lexicon endpoints |

## Stack Patterns by Variant

**If v1 scope remains owner-account, text/link-only (current milestone):**
- Use `app.bsky.feed.getAuthorFeed` (`filter=posts_no_replies`) for incremental feed pulls
- Use `com.atproto.repo.listRecords` (`collection=app.bsky.feed.post`) as canonical reconciliation set for edit/delete detection
- Because this yields deterministic import/reconcile behavior without stream infrastructure

**If future scope adds cross-instance hosting or non-bsky.social PDS accounts:**
- Add identity resolution step (`com.atproto.identity.resolveHandle` + DID doc service endpoint lookup) before calling repo APIs
- Because PDS-targeted endpoints are hosted per account infrastructure, not guaranteed to be one fixed hostname

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `httpx>=0.28.1` | Python 3.12 runtime (current project baseline) | Already validated in current codebase integrations. |
| `django-celery-beat==2.9.0` | Django 5.2 (classifier support listed on PyPI) | Existing scheduler approach remains valid; repo currently appears unpinned and can stay as-is unless you choose to pin. |
| `atproto==0.0.65` (optional) | Python 3.12 (package requires >=3.9,<3.15) | Technically compatible but operationally less stable due pre-1.0 warning. |

## Integration Points with Existing Architecture

- Add a new app (e.g. `apps/bluesky`) following `apps/gadgets` sync separation:
  - `sync.py`: API client + reconciliation logic
  - `tasks.py`: Celery task wrapper with feature flag guard
  - `management/commands/sync_bluesky.py`: manual trigger
  - `admin.py`: sync-now action/button
- Extend `SCHEDULED_TASKS` in `taylor_learns/settings.py` with a `bluesky-sync` periodic task, then continue using `bootstrap_celery_tasks` to materialize schedules.
- Persist source mapping metadata needed for deterministic reconciliation (at minimum: Bluesky post URI, CID, source created timestamp, last seen timestamp, soft-deleted timestamp, raw source payload hash/version).
- Keep import writes idempotent with DB uniqueness on source URI (or DID+rkey), mirroring existing sync safety goals.

## v1 Prescriptive Recommendation

1. **Do not add any new runtime dependency for v1.** Build Bluesky client/reconciliation on existing `httpx` + Celery + `django-celery-beat`.
2. **Use two Bluesky endpoints together:**
   - `app.bsky.feed.getAuthorFeed` for incremental discovery
   - `com.atproto.repo.listRecords` for authoritative edit/delete reconciliation
3. **Keep scheduling in existing beat bootstrap flow** (same operational model as gadgets) and add manual sync via both management command and admin action.
4. **Defer `atproto` SDK, firehose, and media/thread ingestion** until after v1 correctness is proven in production.

## Sources

- https://docs.bsky.app/docs/advanced-guides/api-directory — API host/auth model and service boundaries (official)
- https://docs.bsky.app/docs/advanced-guides/rate-limits — rate-limit behavior for polling strategy (official)
- https://docs.bsky.app/docs/api/app-bsky-feed-get-author-feed — public feed endpoint semantics (official)
- https://docs.bsky.app/docs/api/com-atproto-repo-list-records — repo record listing semantics (official)
- https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/getAuthorFeed.json — parameter/limit/filter contract (official lexicon)
- https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json — pagination/reverse/limit contract (official lexicon)
- https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/post.json — post schema details (text/facets/embed fields)
- https://pypi.org/project/django-celery-beat/ — current release and Django compatibility classifiers
- https://pypi.org/project/atproto/ — optional SDK version and stability caveat context

---
*Stack research for: Bluesky import into existing Django/Wagtail microblog pipeline*
*Researched: 2026-03-19*
