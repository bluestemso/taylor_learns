# Feature Research

**Domain:** Bluesky-to-site microblog mirroring for an existing Django/Wagtail CMS
**Researched:** 2026-03-19
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Single-account source binding (owner DID/handle) | v1 mirrors are expected to map one known source account cleanly | LOW | Store `source_did` + canonical handle; avoid any account-discovery UX in first milestone. |
| Pull-based sync (manual run + scheduled polling) | Mirroring implies both "sync now" control and unattended freshness | MEDIUM | Use existing Celery task path for both trigger types; keep one shared ingestion service for parity. |
| Idempotent import + dedupe by stable source ID | Duplicate posts are the #1 trust failure in mirror tools | MEDIUM | Use AT URI (or DID + collection + rkey) as unique key; upsert, never blind insert. |
| Update propagation (edit existing mirrored entry) | Users expect mirrored content to stay aligned after source edits | MEDIUM | Treat source as canonical; compare normalized text/link payload and update local entry deterministically. |
| Delete propagation with soft-delete locally | Mirrors should hide removed source posts without destructive data loss | MEDIUM | Mark local entry as removed/inactive instead of hard delete; retain mapping/audit metadata. |
| Text + link fidelity for post body | v1 users expect text and outbound links to render correctly | LOW | Keep scope to plain text + links/facets; defer media and threading data models. |
| Sync observability (run status, counts, last successful sync) | Operators need to trust and debug mirroring behavior | LOW | Track fetched/imported/updated/deleted/skipped counts and cursor/checkpoint per run. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Preview + selective import mode before publish | Gives editorial confidence without disabling automation globally | MEDIUM | Add staging state and allow per-item approve/ignore policies. |
| Backfill window controls (e.g., last N days/posts) | Reduces initial feed noise and shortens first sync runtime | LOW | Useful for onboarding existing accounts without importing years of history. |
| Rich embed expansion (images/cards/quotes) | Makes mirrored feed visually closer to Bluesky native experience | HIGH | Requires blob/embed handling and larger content schema surface. |
| Thread/reply context reconstruction | Preserves conversational meaning of replies and quote posts | HIGH | Depends on recursive fetch of referenced posts and cross-record link graph. |
| Near-real-time ingest (firehose/stream-driven) | Improves freshness and reduces polling lag | HIGH | Operationally heavier than scheduled polling; better as post-v1 once base ingest is stable. |
| Bidirectional sync controls (publish edits back upstream) | Enables true multi-home workflows for power users | HIGH | Introduces conflict resolution, auth scope expansion, and higher blast radius. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-account ingestion in v1 | "One pipeline for all team accounts" sounds efficient | Expands auth, ownership, and moderation scope before core reliability is proven | Ship one owner account first; add account abstraction after stable v1 metrics. |
| Firehose-first architecture for launch | Real-time feels more "correct" than polling | Adds infra and ordering complexity early; harder to reason about replay/backfill | Start with deterministic polling + cursor checkpoints; evaluate firehose later. |
| Hard-deleting mirrored rows on source delete | Keeps DB "clean" | Destroys audit trail and makes replay/recovery difficult | Soft-delete + keep source mapping metadata. |
| Full social graph import (likes/reposts/follows) | Requests for "complete Bluesky mirror" | Dilutes milestone goal and introduces moderation/privacy complexity | Restrict v1 to posts only (text + links). |
| Auto-importing old archive by default | Users ask for instant full history | Large imports increase failure risk and clutter site feed unexpectedly | Default to controlled backfill window + explicit operator choice. |

## Feature Dependencies

```
[Single-account source binding]
    └──requires──> [Pull-based sync orchestration]
                         └──requires──> [Checkpoint/cursor persistence]
                                              └──requires──> [Idempotent upsert + dedupe]
                                                                      ├──requires──> [Update propagation]
                                                                      └──requires──> [Soft-delete propagation]

[Text + link fidelity] ──enhances──> [Idempotent upsert + dedupe]

[Sync observability] ──enhances──> [Pull-based sync orchestration]

[Firehose-first architecture] ──conflicts──> [Deterministic polling-based v1 scope]
```

### Dependency Notes

- **Single-account source binding requires pull-based sync orchestration:** the scheduler/manual trigger needs a known canonical source identity.
- **Pull-based sync orchestration requires checkpoint/cursor persistence:** without saved progress, runs re-read too much data and increase duplicate/update ambiguity.
- **Checkpoint/cursor persistence requires idempotent upsert + dedupe:** cursors reduce work, but only idempotent writes guarantee correctness during retries/replays.
- **Idempotent upsert + dedupe requires update + soft-delete propagation:** otherwise mirrored state diverges from source reality over time.
- **Sync observability enhances orchestration:** run metrics are needed to tune schedule frequency and detect regressions.
- **Firehose-first conflicts with deterministic polling v1 scope:** stream ingestion changes ops profile and should not block first release validation.

## MVP Definition

### Launch With (v1)

Minimum viable product — what is needed to validate reliable mirroring.

- [ ] Single-account source binding (owner only) — enforces milestone scope and simplifies auth/risk.
- [ ] Manual + scheduled polling sync using existing job system — enables controlled and automated import.
- [ ] Idempotent upsert keyed by source AT URI — prevents duplicate entries across retries.
- [ ] Update + soft-delete propagation — keeps site mirror aligned with source lifecycle.
- [ ] Text + link import fidelity — delivers useful post rendering with constrained complexity.
- [ ] Sync observability dashboard/logging fields — supports operations and confidence in automation.

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Configurable backfill window — add when initial import pain appears in real usage.
- [ ] Import policy controls (auto-publish vs review) — add if editorial moderation needs emerge.
- [ ] Basic media ingest (images only) — add after text/link pipeline reliability is proven.

### Future Consideration (v2+)

Features to defer until strong workflow fit is established.

- [ ] Thread/reply graph mirroring — defer due to cross-post dependency graph complexity.
- [ ] Firehose-driven near-real-time updates — defer until polling limits are measurable bottlenecks.
- [ ] Multi-account + role-based ownership — defer until product moves beyond personal site model.
- [ ] Bidirectional publishing/sync conflict resolution — defer until one-way mirror is operationally mature.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Idempotent upsert + dedupe | HIGH | MEDIUM | P1 |
| Manual + scheduled polling sync | HIGH | MEDIUM | P1 |
| Update + soft-delete propagation | HIGH | MEDIUM | P1 |
| Single-account source binding | HIGH | LOW | P1 |
| Sync observability | MEDIUM | LOW | P1 |
| Text + link fidelity | HIGH | LOW | P1 |
| Configurable backfill window | MEDIUM | LOW | P2 |
| Import review/approval mode | MEDIUM | MEDIUM | P2 |
| Image/media import | MEDIUM | HIGH | P2 |
| Thread/reply reconstruction | MEDIUM | HIGH | P3 |
| Firehose ingest | LOW (for this milestone) | HIGH | P3 |
| Multi-account support | LOW (for this milestone) | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Bridgy Fed (cross-network bridge) | Typical self-hosted importer pattern | Our Approach |
|---------|-----------------------------------|--------------------------------------|--------------|
| Core mirroring model | Broad protocol bridge with many translation rules | Narrow one-source ingest into local CMS table | Keep scope narrow: one Bluesky source into local microblog entries. |
| Edit/delete behavior | Supports delete propagation; edit support varies by network path | Usually upsert + soft-delete for local reliability | Make deterministic update + soft-delete first-class in v1. |
| Scope breadth | Profiles, interactions, moderation translation, multi-network concerns | Post content only, often polling-based | Stay post-only (text/links) in v1 to maximize reliability and delivery speed. |

## Sources

- Project baseline and milestone scope: `.planning/PROJECT.md` (HIGH confidence).
- Bluesky HTTP reference for author feed and record listing (`app.bsky.feed.getAuthorFeed`, `com.atproto.repo.listRecords`): https://docs.bsky.app/docs/api/app-bsky-feed-get-author-feed, https://docs.bsky.app/docs/api/com-atproto-repo-list-records (HIGH confidence).
- AT Protocol repository/record model (record keys, repository semantics): https://atproto.com/specs/repository, https://atproto.com/specs/record-key (HIGH confidence).
- Bluesky rate-limit guidance for polling/throughput planning: https://docs.bsky.app/docs/advanced-guides/rate-limits (HIGH confidence).
- Ecosystem reference for broad bridge behavior and complexity trade-offs: https://fed.brid.gy/docs (MEDIUM confidence; product docs, not a formal protocol spec).
- ATProto JS client capabilities and current auth direction: https://www.npmjs.com/package/@atproto/api (MEDIUM confidence; package documentation, rapidly evolving).

---
*Feature research for: Bluesky-to-CMS microblog import (subsequent milestone)*
*Researched: 2026-03-19*
