# Project Research Summary

**Project:** Taylor Learns (v1.0 Bluesky Microblog Import)
**Domain:** Bluesky-to-CMS microblog mirroring in an existing Django/Wagtail app
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Executive Summary

This milestone is a reliability-first content ingestion feature, not a social platform build. The recommended implementation is to mirror one owner Bluesky account into existing Wagtail `MicroPostPage` entries using deterministic polling, idempotent reconciliation, and existing Celery infrastructure. Expert pattern for this class of product is narrow scope first (single source, text/links only), with strict source identity and lifecycle parity (create/update/soft-delete) before adding richer media or real-time streaming.

The strongest recommendation is to avoid adding new platform primitives in v1: keep Django/Wagtail as system of record, run sync jobs through existing Celery + `django-celery-beat`, and use `httpx` XRPC calls to `com.atproto.repo.listRecords` plus `app.bsky.feed.getAuthorFeed` where useful for incremental discovery. Architecturally, separate decision logic (`reconcile.py`) from mutation logic (`publish.py`) and route all triggers (admin, command, schedule) through one orchestration path.

Primary risks are identity drift (handle-based keys), duplicate imports from non-idempotent runs, lifecycle drift when edits/deletes are ignored, and race conditions from overlapping jobs. Mitigations are explicit and actionable: DID/URI-backed unique constraints, transactional upserts, `cid`-based change detection, soft-delete semantics, per-source single-flight locking, and typed failure telemetry.

## Key Findings

### Recommended Stack

Research converges on reusing the existing app stack for v1 and deferring optional SDK/streaming complexity. The stack recommendation is conservative by design to minimize migration and operational risk while maximizing correctness.

**Core technologies:**
- Django 5.2.x + Wagtail 7.2.x: system of record for imported microblog pages; keeps editorial and rendering workflows unchanged.
- Celery 5.x + Redis 7.x: manual and scheduled sync execution off-request with existing retry/ops patterns.
- `httpx>=0.28.1`: direct Bluesky XRPC access with existing networking conventions in this repo.
- `django-celery-beat` 2.9.0: schedule sync cadence via DB/admin without redeploys.

**Critical version notes:**
- `atproto==0.0.65` is compatible but explicitly pre-1.0 and should stay optional/deferred.

### Expected Features

The MVP is tightly scoped and sequencing-sensitive: identity contract and orchestration first, then deterministic import behavior, then lifecycle parity, with observability from day one.

**Must have (table stakes):**
- Single-account source binding (owner DID/handle metadata).
- Manual + scheduled sync through one ingestion path.
- Idempotent upsert/dedupe keyed by stable source URI (or DID+rkey).
- Update propagation and soft-delete propagation.
- Text + link fidelity for post body/facets.
- Sync observability (counts, status, last success, checkpoints).

**Should have (competitive):**
- Configurable backfill window.
- Optional review/selective import mode.
- Basic image ingest after core reliability.

**Defer (v2+):**
- Firehose near-real-time ingestion.
- Thread/reply graph reconstruction.
- Multi-account ownership model.
- Bidirectional publishing/sync.

### Architecture Approach

The recommended architecture is a new isolated `apps/bluesky/` integration app with strict boundaries: `client.py` (API semantics), `reconcile.py` (pure diff), `publish.py` (Wagtail mutations), `sync.py` (run orchestration), and `tasks.py`/management/admin as triggers. Data ownership stays clean by storing source sync state and mappings in new Bluesky models instead of coupling metadata into `apps/content` models. This supports deterministic replay, easier tests, and safer retries.

**Major components:**
1. Trigger layer (admin, command, beat/task) -> invokes one sync service path only.
2. Sync domain (`client`, `reconcile`, `publish`, `sync`) -> fetch, diff, apply, summarize.
3. Persistence (`BlueskySource`, `BlueskyPostMap`, existing `MicroPostPage`) -> durable mapping, lifecycle state, published content.

### Critical Pitfalls

1. **Handle-based primary keys** -> avoid by keying on DID + URI/rkey and treating handle as display metadata only.
2. **Non-idempotent imports** -> avoid with DB uniqueness + transactional upserts + replay-safe checkpoints.
3. **Missing edit/delete reconciliation** -> avoid with `cid` tracking and deterministic soft-delete when source disappears.
4. **Concurrent sync races** -> avoid with per-source lock and atomic cursor/checkpoint updates.
5. **Opaque failures** -> avoid with typed error classes, structured run records, and bounded retry policy.

## Implications for Roadmap

Based on combined research, suggested phase structure:

### Phase 1: Source Contract and Data Model Foundations
**Rationale:** Durable identity and ordering policy are prerequisites for every later sync decision.
**Delivers:** `BlueskySource` + `BlueskyPostMap` schema, DID-first source contract, provenance fields, stable ordering (`sort_at`) policy.
**Addresses:** Single-account binding, foundational observability fields.
**Avoids:** Handle-key drift, audit/provenance gaps, ordering instability.

### Phase 2: Deterministic Import Engine (Create/Update Path)
**Rationale:** Core value is reliable import without duplicates; build the idempotent write path early.
**Delivers:** `client.py` pagination/normalization, reconciliation diff for create/update/no-op, transactional publish/upsert integration.
**Uses:** Existing `httpx`, Django ORM, Wagtail models.
**Implements:** Snapshot reconciliation + trigger/worker separation patterns.
**Avoids:** Duplicate rows, facet/text transform regressions.

### Phase 3: Lifecycle Parity and Entry Points
**Rationale:** v1 correctness requires mirrored edits/deletes and operator controls, not just initial ingest.
**Delivers:** Soft-delete/unpublish reconciliation, manual command/admin trigger, shared `run_sync` orchestration summaries.
**Addresses:** Update + delete propagation, operational trust.
**Avoids:** Stale/deleted source posts remaining live.

### Phase 4: Scheduling, Concurrency Safety, and Operational Hardening
**Rationale:** Automation should come after correctness path exists; hardening prevents data corruption under real operations.
**Delivers:** Celery beat schedule wiring, per-source lock/single-flight execution, backoff/retry classification, run dashboards/alerts.
**Uses:** Existing Celery + Redis + `django-celery-beat`.
**Avoids:** Race conditions, retry storms, low-diagnosability failures.

### Phase Ordering Rationale

- Dependencies demand identity/model before ingestion logic, and ingestion logic before lifecycle/scheduling hardening.
- Architecture supports this order naturally (`models` -> `client/reconcile` -> `publish/sync` -> `tasks/ops`).
- The ordering directly neutralizes top pitfalls in the sequence they typically surface in production.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** Bluesky facet/link parsing edge cases (UTF-8 byte indexing, canonical link extraction test corpus).
- **Phase 4:** Locking strategy choice (Redis lock vs DB advisory lock) and retry budget tuning under rate limits.

Phases with standard patterns (can likely skip research-phase):
- **Phase 1:** Django model/schema and provenance patterns are well-established.
- **Phase 3:** Admin command + management command + shared service orchestration mirrors existing repo patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Strong alignment with existing codebase and official Bluesky/Django/Celery docs; minimal novelty in v1 stack. |
| Features | MEDIUM | Prioritization is coherent and source-backed, but differentiator choices remain product-opinion sensitive. |
| Architecture | MEDIUM | Pattern quality is high, but final fit depends on exact `MicroPostPage` mutation constraints in this repo. |
| Pitfalls | HIGH | Risks are concrete, repeatedly observed in ingestion systems, and supported by official protocol/framework guidance. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- Exact `MicroPostPage` publish/unpublish contract details and required provenance field placement should be validated early in phase planning.
- Final auth method for Bluesky access (app password vs token flow specifics) needs explicit operational policy before production rollout.
- Initial sync/backfill default window should be validated against real account history to avoid long first-run jobs and feed shock.

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` - stack and version recommendations based on official docs + repo fit.
- `.planning/research/FEATURES.md` - MVP table stakes, dependency chain, and deferral boundaries.
- `.planning/research/ARCHITECTURE.md` - component boundaries, data flow, and build-order guidance.
- `.planning/research/PITFALLS.md` - failure modes, prevention playbooks, and phase mapping.
- Official Bluesky/ATProto docs and lexicons (`docs.bsky.app`, `atproto.com/specs`) - API semantics, identity, and lifecycle contracts.

### Secondary (MEDIUM confidence)
- `django-celery-beat` release/compatibility references and Wagtail model workflow docs for operational integration assumptions.
- Bridgy Fed product docs used as comparative complexity signal for scope control.

### Tertiary (LOW confidence)
- None material; low-confidence claims were avoided in recommendations.

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
