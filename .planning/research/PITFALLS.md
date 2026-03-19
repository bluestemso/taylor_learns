# Pitfalls Research

**Domain:** Bluesky-to-CMS microblog ingestion for an existing Django/Wagtail site
**Researched:** 2026-03-19
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Using handle-based identity as the primary key

**What goes wrong:**
Imported rows are keyed by handle (or handle-form `at://` URIs), then drift or duplicate when the account handle changes.

**Why it happens:**
Handles are human-friendly and easy to display, so teams accidentally use them as durable IDs.

**How to avoid:**
Key all imported records by stable source identity (`did` + record URI/rkey), store handle only as display metadata, and persist the source `cid` for change detection.

**Warning signs:**
Duplicate entries after a handle change, failed lookups by source URI, or import logic that references `@handle` instead of `did:*`.

**Phase to address:**
Phase 1 - Source contract and CMS mapping.

---

### Pitfall 2: Non-idempotent sync runs create duplicates

**What goes wrong:**
Manual and scheduled sync both create new CMS entries for the same Bluesky post.

**Why it happens:**
The importer uses content text or timestamp matching instead of a strict unique source key and upsert path.

**How to avoid:**
Add a unique DB constraint on source post URI (or DID + rkey), implement transactional upsert semantics, and keep sync checkpoints/cursors per source account.

**Warning signs:**
More CMS rows than source posts, repeated imports after retry, or racey behavior when two sync jobs overlap.

**Phase to address:**
Phase 2 - Deterministic import engine.

---

### Pitfall 3: Edits and deletes are treated as out-of-scope after initial import

**What goes wrong:**
CMS content diverges from Bluesky: edited source posts stay stale, deleted source posts remain publicly visible.

**Why it happens:**
Teams optimize for "initial ingest works" and skip lifecycle reconciliation (update and soft-delete).

**How to avoid:**
Track source `cid` and last-seen revision, re-fetch and compare records during polling windows, and implement deterministic soft-delete behavior when source records disappear.

**Warning signs:**
Known deleted Bluesky posts still live on site, no code path for delete reconciliation, or no model fields for source revision state.

**Phase to address:**
Phase 3 - Reconciliation and lifecycle sync.

---

### Pitfall 4: Incorrect time semantics break feed ordering

**What goes wrong:**
Imported posts jump unexpectedly in chronology (future timestamps, bulk import clumping, or unstable sort order).

**Why it happens:**
Importer assumes `createdAt` is always trustworthy and ignores indexing/ingestion time fallback behavior.

**How to avoid:**
Persist both source `createdAt` and ingest/index time, compute a stable `sort_at` policy (source time unless invalid/future, else ingest time), and test with skewed/future data.

**Warning signs:**
New imports appearing above newer real posts, negative/implausible dates, or brittle ordering after backfill.

**Phase to address:**
Phase 1 - Data model mapping and ordering rules.

---

### Pitfall 5: Rich text and links are parsed as plain text shortcuts

**What goes wrong:**
Links are malformed, mentions are wrong, or unicode-heavy posts render incorrectly after import.

**Why it happens:**
Developers treat post text as simple strings and skip Bluesky facet semantics and UTF-8 byte-index assumptions.

**How to avoid:**
For v1 (text + links), parse and store canonical link targets from source facets where present, treat source text as untrusted input, and sanitize rendered output in CMS templates.

**Warning signs:**
Broken links in imported posts, mismatch between Bluesky-rendered text and site-rendered text, or emoji-containing posts failing tests.

**Phase to address:**
Phase 2 - Transform and render contract.

---

### Pitfall 6: Sync job concurrency races corrupt import state

**What goes wrong:**
Overlapping manual and scheduled jobs race on cursor/checkpoint updates and write inconsistent data.

**Why it happens:**
Celery jobs are scheduled correctly but without distributed locking or run-serialization around shared source state.

**How to avoid:**
Add a per-source lock (Redis or DB advisory lock), make cursor/checkpoint writes atomic, and enforce single active sync per account.

**Warning signs:**
Intermittent duplicates, cursor moving backward, or two workers logging the same source window simultaneously.

**Phase to address:**
Phase 4 - Operational hardening.

---

### Pitfall 7: Error handling is too broad to recover safely

**What goes wrong:**
Failures are logged as generic errors, operators cannot classify retryable vs permanent failures, and bad data keeps replaying.

**Why it happens:**
`except Exception` patterns collapse protocol, network, auth, and validation failures into one bucket.

**How to avoid:**
Use typed error classes, store structured failure codes/metadata on each sync attempt, and implement bounded retries with explicit dead-letter/review paths.

**Warning signs:**
High failure counts with no root cause, repeated retries with identical payloads, or support runbooks that start with "re-run until it works".

**Phase to address:**
Phase 4 - Observability and failure policy.

---

### Pitfall 8: Bypassing CMS draft/live and audit expectations

**What goes wrong:**
Auto-published imports skip intended editorial/audit semantics, or future workflow adoption becomes expensive refactor work.

**Why it happens:**
Teams write directly to content fields without a clear persistence contract for publish state, revision history, and provenance.

**How to avoid:**
Define import provenance fields (`source_uri`, `source_cid`, `imported_at`, `sync_run_id`), align auto-publish behavior with model publish fields, and keep optional revision hooks for later moderation milestones.

**Warning signs:**
No way to trace which sync created an entry, no provenance in admin, or inability to safely re-run import after schema changes.

**Phase to address:**
Phase 1 - CMS model contract, then Phase 3 verification.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Match posts by text+timestamp | Quick first import | Unfixable duplicate/merge bugs | Never |
| Store only latest snapshot (no source CID/revision) | Fewer columns now | Cannot diff edits or explain changes | Never |
| No per-source lock on sync task | Simple Celery setup | Race conditions and non-determinism | Never |
| Generic "sync failed" log only | Fast implementation | Slow incident response, hidden data corruption | Never |
| Skip reconciliation of deletions in v1 | Faster MVP demo | Public trust issues and manual cleanup | Only for throwaway prototype, not this milestone |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Bluesky identity | Treat handle as immutable ID | Use DID as durable identity; handle is display metadata |
| Bluesky feed pagination | Drop/overwrite cursor incorrectly between runs | Persist cursor/checkpoint atomically per account |
| Bluesky lifecycle | Import creates only, no update/delete pass | Implement create/update/soft-delete reconciliation |
| Celery scheduling | Allow overlapping sync windows | Use lock + single-flight sync execution |
| Wagtail/Django content model | Write fields without provenance/revision plan | Store source metadata and sync run lineage on each entry |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full backfill on every scheduled run | Sync duration grows over time | Incremental cursor-based polling | Usually after a few hundred/thousand posts |
| Per-record network round-trips in tight loops | Slow jobs, timeout spikes | Batch where possible; bounded concurrency + retries | During retries or degraded upstream latency |
| Unbounded retry storms on 429/5xx | Queue bloat and duplicate processing | Exponential backoff with jitter and retry budgets | During upstream rate-limit events |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing primary account password for sync auth | Account compromise blast radius | Use app password/OAuth tokens with least privilege and rotation |
| Rendering imported text/links without sanitization | XSS or content injection path | Treat source as untrusted; sanitize/escape in templates |
| Overexposed sync admin actions | Unauthorized publishing/deletion via internal tools | Require staff authz and audit logging for manual sync controls |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent partial sync failures | Feed looks random/incomplete | Show sync status, last successful run, and failure reason in admin |
| Imported post order disagrees with Bluesky | User distrusts canonical site feed | Publish explicit ordering policy (`sort_at`) and test against edge cases |
| Deleted source posts still visible on site | Trust and correctness erosion | Soft-delete promptly and mark provenance in admin |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Identity mapping:** Using DID-backed source keys, not handle-based keys.
- [ ] **Idempotency:** Unique constraint plus transactional upsert verified under repeated runs.
- [ ] **Lifecycle parity:** Edit and delete reconciliation paths tested, including soft-delete behavior.
- [ ] **Ops safety:** Single-flight locking and cursor atomicity validated with concurrent trigger test.
- [ ] **Observability:** Structured sync result records include counts, latency, and typed failure reasons.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Duplicate imports due to bad keying | MEDIUM | Add durable key + unique index, run dedupe migration keyed by source URI, re-run backfill for canonical state |
| Missing delete/edit reconciliation | MEDIUM | Add reconciliation pass, diff source vs CMS by source URI/CID, soft-delete or update mismatches, then schedule integrity checks |
| Cursor/state corruption from concurrent jobs | HIGH | Freeze schedulers, restore last known-good checkpoint, replay from bounded window, then enable distributed lock |
| Generic failure logs with unknown root cause | MEDIUM | Introduce typed errors + structured run logs, reprocess failed windows by class, and add alerting thresholds |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Handle-based identity keys | Phase 1 - Source contract and model mapping | Schema uses DID/source URI unique keys; handle change simulation passes |
| Non-idempotent duplicate imports | Phase 2 - Deterministic import engine | Re-running same window is a no-op except expected updates |
| Missing edit/delete parity | Phase 3 - Reconciliation and lifecycle sync | Contract tests cover source edit and delete propagation |
| Ordering drift from timestamp misuse | Phase 1 - Ordering policy definition | Fixtures with future/skewed timestamps sort predictably |
| Rich text/link parsing regressions | Phase 2 - Transform and render contract | Unicode/link fixture snapshots match expected render |
| Concurrent sync race conditions | Phase 4 - Operational hardening | Forced concurrent triggers still produce one authoritative run |
| Opaque failure handling | Phase 4 - Observability and retry policy | Dashboard shows typed failure classes and retry outcomes |
| CMS provenance/audit gaps | Phase 1 + Phase 3 | Admin shows source lineage and import run metadata per entry |

## Sources

- AT Protocol: AT URI scheme (handle durability caveat, DID recommendation) - https://atproto.com/specs/at-uri-scheme (HIGH)
- AT Protocol: Sync guide (DID/repo identifiers, record URI/CID model) - https://atproto.com/guides/sync (HIGH)
- AT Protocol: Repository spec (deletions, repo mutation semantics) - https://atproto.com/specs/repository (HIGH)
- Bluesky docs: Viewing feeds (cursor pagination and limits) - https://docs.bsky.app/docs/tutorials/viewing-feeds (HIGH)
- Bluesky docs: Rate limits (429 behavior and evolving limits) - https://docs.bsky.app/docs/advanced-guides/rate-limits (HIGH)
- Bluesky docs: Resolving identities (identity caching and DID/handle guidance) - https://docs.bsky.app/docs/advanced-guides/resolving-identities (HIGH)
- Bluesky docs: Posts + Rich text facets + Timestamps (text/link semantics and ordering guidance) - https://docs.bsky.app/docs/advanced-guides/posts, https://docs.bsky.app/docs/advanced-guides/post-richtext, https://docs.bsky.app/docs/advanced-guides/timestamps (HIGH)
- Bluesky docs: Backfill and firehose operational notes - https://docs.bsky.app/docs/advanced-guides/backfill, https://docs.bsky.app/docs/advanced-guides/firehose (MEDIUM for this milestone, since v1 is polling-based)
- Django docs: transaction and `on_commit` patterns for reliable side effects - https://docs.djangoproject.com/en/stable/topics/db/transactions/ (HIGH)
- Wagtail docs: model live state and snippet draft/revision workflow behavior - https://docs.wagtail.org/en/stable/reference/models.html, https://docs.wagtail.org/en/stable/topics/snippets/features.html (MEDIUM; model-level applicability depends on current microblog model type)
- Internal codebase concerns (race conditions + broad exception handling patterns): `.planning/codebase/CONCERNS.md` (HIGH)

---
*Pitfalls research for: Bluesky-to-CMS microblog import milestone*
*Researched: 2026-03-19*
