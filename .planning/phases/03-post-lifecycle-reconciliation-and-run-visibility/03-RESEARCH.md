# Phase 3: Post Lifecycle Reconciliation and Run Visibility - Research

**Researched:** 2026-03-20
**Domain:** Bluesky record lifecycle reconciliation in Django/Wagtail sync pipeline
**Confidence:** HIGH

## User Constraints

`CONTEXT.md` is not present for this phase, so there are no additional locked decisions beyond roadmap + requirements.

### Locked Decisions
- Phase scope (from roadmap): "Keep mirrored entries aligned with Bluesky edits/deletes and expose sync outcomes."
- Must satisfy requirement IDs: LIFE-01, LIFE-02, LIFE-03.
- Build on existing Phase 2 architecture (deterministic import + post map + command-driven sync).

### Claude's Discretion
- Data model for run visibility (single run model vs source-level last-run snapshot + history).
- Exact reconciliation flow for detecting deletions under polling constraints.
- Where to expose run outcomes (admin changelist/detail, command output, both).

### Deferred Ideas (OUT OF SCOPE)
- Scheduling and overlap prevention (Phase 4: SYNC-03, LIFE-04).
- Firehose/event-stream ingestion.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LIFE-01 | User can see Bluesky post edits reflected in the corresponding microblog entry after sync. | Keep CID-based change detection (`updated`) + call existing `upsert_and_publish_micro_post` update path; preserve map row and publish revision. |
| LIFE-02 | User can have deleted Bluesky posts soft-removed (unpublished/marked removed) in the CMS after sync. | Use map-to-remote set reconciliation after paginated `listRecords`; for missing mapped URIs, call Wagtail `unpublish()` and mark mapping as removed metadata (or delete map only if visibility/history requirements permit). |
| LIFE-03 | User can view sync run outcomes including counts for imported, updated, removed, and skipped posts. | Add explicit run-result persistence model + admin visibility + command output with deterministic counters including `removed`. |
</phase_requirements>

## Summary

The current implementation already has the core primitives for edit reconciliation: `source_uri` identity mapping (`BlueskyPostMap`), CID change classification (`created`/`updated`/`skipped`), and deterministic publish/update behavior in `upsert_and_publish_micro_post`. This means LIFE-01 should be delivered by extending (not replacing) the existing Phase 2 flow in `apps/bluesky/sync.py`, `apps/bluesky/reconcile.py`, and `apps/bluesky/publish.py`.

The major Phase 3 addition is deletion handling and run visibility. Bluesky `com.atproto.repo.listRecords` returns current records only, with pagination and max limit 100; deleted records are not tombstoned in repository state, so deletion detection under polling is a set-difference problem (local mapped URIs minus currently returned remote URIs for the source/collection). After detection, Wagtail supports unpublishing pages via `unpublish(set_expired=False, ...)`, which is the correct "soft-remove" semantic for LIFE-02.

For LIFE-03, command stdout alone is insufficient "view" for ongoing operations; this codebase already uses persistent sync status patterns in `apps/gadgets` (`last_sync_status`, `last_synced_at`, etc.). For Bluesky, implement run-level persistence (preferred: append-only run history with counters and timestamps) and expose it in Django admin for operators.

**Primary recommendation:** Keep Phase 2 reconciliation logic intact, add a dedicated deletion-reconciliation pass and a persistent `BlueskySyncRun` model with `imported/updated/removed/skipped/failed` counters surfaced in admin and command output.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2.8 (project baseline; PyPI latest 6.0.3) | ORM, migrations, admin, management commands | Existing project stack and all current Bluesky code paths are Django-native. |
| Wagtail | 7.2.3 (project baseline; PyPI latest 7.3.1) | MicroPost page publish/unpublish lifecycle | Existing `MicroPostPage` publishing already uses Wagtail revisions/live state. |
| httpx | 0.28.1 | Bluesky XRPC HTTP client | Already used by `apps/bluesky/client.py`, sufficient for paginated list calls. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| AT Protocol lexicons (com.atproto.repo.*) | current main lexicon schema | Contract for list/get record behavior | For endpoint limits, pagination, and response contract validation. |
| Django TestCase test runner (`manage.py test`) | project default | Regression protection for lifecycle + counters | For all reconciliation contract tests in `apps/bluesky/tests/`. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Polling `com.atproto.repo.listRecords` + set reconciliation | Firehose / subscribeRepos stream | Better freshness but higher ops complexity; explicitly out of scope for this milestone. |
| Run-history model | Only source-level `last_*` fields | Simpler schema, but weak auditability and poorer operator visibility per-run. |

**Installation:**
```bash
# No new package required for Phase 3 on current architecture.
```

**Version verification:**
- Verified via PyPI JSON on 2026-03-20:
  - `django` latest `6.0.3` (uploaded 2026-03-03)
  - `wagtail` latest `7.3.1` (uploaded 2026-03-03)
  - `httpx` latest `0.28.1` (uploaded 2024-12-06)
- Project baseline remains `Django>=5.2.8`, `wagtail>=7.2.3`, `httpx>=0.28.1` (`pyproject.toml`).

## Architecture Patterns

### Recommended Project Structure
```
apps/bluesky/
|-- models.py                  # post map + sync run model (new)
|-- sync.py                    # orchestration: import/update + deletion reconcile + counters
|-- reconcile.py               # classification + deletion candidate helpers
|-- publish.py                 # create/update/unpublish operations for MicroPostPage
|-- admin.py                   # source + run visibility in admin
|-- management/commands/
|   `-- sync_bluesky.py        # operator entrypoint with deterministic summary output
`-- tests/
    |-- test_sync_bluesky_command.py
    |-- test_reconcile.py
    `-- test_publish.py
```

### Pattern 1: Two-pass reconciliation (upsert pass + remove pass)
**What:** First process returned records (`created/updated/skipped`), then compute missing mapped URIs and soft-remove them.
**When to use:** Polling APIs where deletion tombstones are absent.
**Example:**
```typescript
// Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json
// listRecords supports cursor pagination and max limit 100;
// fetch all pages for app.bsky.feed.post, collect remote URIs,
// then local_map_uris - remote_uris => deletion candidates.
```

### Pattern 2: Keep URI as canonical identity, CID as version fingerprint
**What:** Use `source_uri` for stable mapping and `source_cid` to detect edits.
**When to use:** Any rerunnable sync where dedupe and edits must both be deterministic.
**Example:**
```python
# Source: apps/bluesky/reconcile.py
post_map = BlueskyPostMap.objects.filter(source_uri=source_uri).first()
if post_map is None:
    return "created"
if post_map.source_cid != source_cid:
    return "updated"
return "skipped"
```

### Pattern 3: Soft-remove via Wagtail unpublish
**What:** Unpublish mirrored `MicroPostPage` rather than hard delete.
**When to use:** External source deletion should be reversible/auditable and not break page history.
**Example:**
```python
# Source: Wagtail model reference (DraftStateMixin.unpublish)
micro_post.unpublish(set_expired=False, log_action=True)
```

### Anti-Patterns to Avoid
- **Single-page polling:** Treating one `listRecords` page as complete repo state will cause false deletions.
- **Hard delete of content/map on first miss:** Destroys auditability and can overreact to transient API gaps.
- **Counter drift:** Incrementing counters outside deterministic branches causes unreliable LIFE-03 visibility.
- **Replacing Phase 2 flow:** Rewrites increase risk; extend current orchestration instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Edit detection | Custom text diff engine | Existing CID comparison in map (`source_cid`) | CID already represents record content version in AT repo responses. |
| Soft removal | Ad-hoc boolean flags without lifecycle integration | Wagtail `unpublish()` and live state | Native Wagtail draft/live lifecycle, consistent with page serving behavior. |
| API contracts | Inferred endpoint behavior | Official lexicon contracts (`com.atproto.repo.listRecords`) | Explicit max limit, cursor, and response fields reduce protocol drift bugs. |
| Run visibility storage | Free-form JSON logs only | Structured Django model counters + timestamps | Queryable admin/reporting, testable deterministic fields. |

**Key insight:** Phase 3 is reconciliation work, not new ingestion architecture; leverage existing map/CID/Wagtail primitives and add only missing lifecycle/reporting layers.

## Common Pitfalls

### Pitfall 1: False delete classification from partial pagination
**What goes wrong:** Posts on later cursor pages are treated as deleted.
**Why it happens:** `listRecords` max `limit` is 100 and requires cursor iteration.
**How to avoid:** Always exhaust cursor pages before computing remote URI set.
**Warning signs:** `removed` spikes whenever account has >100 posts.

### Pitfall 2: Unpublish without map lifecycle strategy
**What goes wrong:** Reconciliation repeatedly attempts to remove already-removed content, or cannot restore correctly on reappearance.
**Why it happens:** No explicit removed-state handling in map/run flow.
**How to avoid:** Define deterministic rules (e.g., map retained with removed marker/timestamp).
**Warning signs:** Same URI counted as removed on every run.

### Pitfall 3: Counter semantics mismatch with roadmap requirement language
**What goes wrong:** Output still reports `failed` but not `removed`, or remaps `created` inconsistently.
**Why it happens:** Legacy counter contract from Phase 2 not updated holistically.
**How to avoid:** Normalize single source of truth for counters: imported/updated/removed/skipped(+failed internal).
**Warning signs:** Command output and persisted run record disagree.

### Pitfall 4: Using source `indexedAt` ordering as deletion truth
**What goes wrong:** Older posts outside fetch window are misclassified removed.
**Why it happens:** Treating time window as full-state snapshot.
**How to avoid:** Reconcile against full collection scope relevant to mirrored set, not recent window only.
**Warning signs:** Historical posts disappear after limiting sync scope.

## Code Examples

Verified patterns from official and in-repo sources:

### Bluesky listRecords contract limits
```json
// Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json
"limit": { "type": "integer", "minimum": 1, "maximum": 100, "default": 50 },
"cursor": { "type": "string" },
"reverse": { "type": "boolean" }
```

### Existing deterministic sync counter pattern
```python
# Source: apps/bluesky/sync.py
counters = {"imported": 0, "updated": 0, "skipped": 0, "failed": 0}
operation = classify_record_operation(source_uri=source_uri, source_cid=source_cid)
```

### Existing upsert behavior for edited posts
```python
# Source: apps/bluesky/publish.py
micro_post.body = stream_body
micro_post.save()
micro_post.save_revision().publish()
post_map.source_cid = source_cid
post_map.save(update_fields=["source_cid", "updated_at", ...])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Import-only sync with no deletion pass | Reconciliation pipeline should include explicit remove pass | Phase 3 scope | Keeps mirror lifecycle parity with source deletions. |
| Command-only ephemeral output | Persisted run-level sync results + admin visibility | Phase 3 target | Operator can inspect run history, not just latest terminal output. |
| Ad-hoc duplicate prevention | URI identity + CID versioning map | Implemented in Phase 2 | Reliable reruns and edit detection already solved. |

**Deprecated/outdated:**
- Treating one-page `listRecords(limit=100)` as authoritative account state.
- Counting only `imported/updated/skipped/failed` for lifecycle-complete reporting.

## Open Questions

1. **Should removed entries stay mapped or should mapping rows be deleted?**
   - What we know: keeping history improves visibility and avoids repeated remove attempts.
   - What's unclear: preferred restore behavior if a previously removed URI reappears.
   - Recommendation: retain map row and add removed metadata (or equivalent) for deterministic lifecycle state.

2. **What is the exact UI expectation for "view sync run outcomes"?**
   - What we know: command output exists today; requirement language suggests inspectable view.
   - What's unclear: whether admin-only view is sufficient for v1.
   - Recommendation: implement admin changelist/detail for run history in Phase 3; expand to frontend only if explicitly requested.

3. **Counter contract for failures in requirement-facing view**
   - What we know: requirement mandates imported/updated/removed/skipped.
   - What's unclear: whether `failed` must also be displayed.
   - Recommendation: persist `failed` internally for diagnostics; keep required four counters as primary UI fields.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django test runner (`manage.py test`) |
| Config file | none (uses Django settings/test discovery) |
| Quick run command | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` |
| Full suite command | `make test` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LIFE-01 | CID change updates corresponding MicroPostPage content after sync | unit/integration | `make test ARGS='apps.bluesky.tests.test_publish apps.bluesky.tests.test_sync_bluesky_command'` | ✅ |
| LIFE-02 | Missing remote mapped post is soft-removed (unpublished) after sync | integration | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` | ❌ Wave 0 (new deletion-focused tests needed) |
| LIFE-03 | Run outcomes visible with imported/updated/removed/skipped counters | unit/integration | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` | ❌ Wave 0 (run-visibility model/admin/command assertions needed) |

### Sampling Rate
- **Per task commit:** `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'`
- **Per wave merge:** `make test ARGS='apps.bluesky.tests'`
- **Phase gate:** `make test`

### Wave 0 Gaps
- [ ] `apps/bluesky/tests/test_sync_lifecycle_reconciliation.py` - deletion reconciliation and removed counter scenarios
- [ ] `apps/bluesky/tests/test_sync_run_visibility.py` - persisted run summary/admin visibility assertions
- [ ] `apps/bluesky/tests/test_sync_bluesky_command.py` updates - include `removed` in rendered command summary

## Sources

### Primary (HIGH confidence)
- Project codebase:
  - `apps/bluesky/sync.py`
  - `apps/bluesky/reconcile.py`
  - `apps/bluesky/publish.py`
  - `apps/bluesky/models.py`
  - `apps/bluesky/tests/test_sync_bluesky_command.py`
  - `apps/content/models.py`
- AT Protocol lexicon (official): https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json
- AT Protocol repository spec (official): https://atproto.com/specs/repository
- Wagtail model reference (official): https://docs.wagtail.org/en/stable/reference/models.html

### Secondary (MEDIUM confidence)
- Bluesky endpoint page (summary-level, less detailed than lexicon): https://docs.bsky.app/docs/api/com-atproto-repo-list-records

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - grounded in current repository implementation + verified package metadata
- Architecture: HIGH - directly derived from existing Phase 2 code paths and official protocol limits
- Pitfalls: MEDIUM-HIGH - protocol and lifecycle constraints are verified; exact product/UI choices still discretionary

**Research date:** 2026-03-20
**Valid until:** 2026-04-19
