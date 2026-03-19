# Phase 2: Deterministic Import and Auto-Publish - Research

**Researched:** 2026-03-19
**Domain:** Deterministic Bluesky-to-Wagtail import pipeline (manual sync, dedupe, text/link fidelity, auto-publish)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

No `02-CONTEXT.md` exists for this phase, so there are no additional locked decisions/discretion notes/deferred ideas to copy verbatim.

Planning constraints are therefore taken from the roadmap + requirements + milestone scope:
- Must satisfy `SYNC-02`, `SYNC-04`, `PUBL-01`, `PUBL-02`, `PUBL-03` in this phase.
- Keep milestone scope to text/link import only (no media/relationship modeling).
- Reuse existing Django/Wagtail/Celery patterns rather than introducing new platforms.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SYNC-02 | User can run a manual sync that imports new Bluesky posts into microblog entries. | Add `sync_bluesky` management command patterned after `apps/gadgets/management/commands/sync_gadgets.py`; route command to one `run_sync()` orchestration service in `apps/bluesky/`. |
| SYNC-04 | User can re-run sync safely without creating duplicate microblog entries. | Persist per-post source mapping with unique key on Bluesky record URI (or DID+rkey) and use transactional upsert (`update_or_create`/equivalent) instead of create-only writes. |
| PUBL-01 | User can see Bluesky post text rendered accurately in imported microblog entries. | Normalize `app.bsky.feed.post` text directly from record payload and map into `MicroPostPage.body` paragraph content without lossy transforms. |
| PUBL-02 | User can see Bluesky links preserved in imported microblog entries. | Use `app.bsky.richtext.facet#link` data (UTF-8 byte indexed) to build anchor tags from canonical facet `uri` values; avoid naive regex-only extraction. |
| PUBL-03 | User can have imported entries auto-published without manual review. | Use Wagtail publish path immediately after page create/update (`save_revision().publish()` pattern already used in project bootstrap command). |
</phase_requirements>

## Summary

Phase 2 should be planned as a single deterministic import path: manual trigger -> fetch Bluesky posts -> reconcile against local source mappings -> publish/create/update `MicroPostPage` entries -> return run summary. The current codebase already provides the shape for this in `apps/gadgets/sync.py` and `apps/gadgets/management/commands/sync_gadgets.py`; reusing this pattern keeps operator ergonomics and error handling consistent.

The central correctness decision is deduplication keying. Official ATProto lexicons show `com.atproto.repo.listRecords` returns stable per-record `uri` and `cid`; using `uri` as the unique mapping key and `cid` for change detection gives replay-safe behavior for repeated manual runs. This directly satisfies `SYNC-04` and avoids fragile text/timestamp matching.

For text/link fidelity, treat Bluesky record content as source-of-truth and facets as canonical annotations. Official richtext docs and lexicons confirm facet indices are UTF-8 byte offsets and links are carried as `app.bsky.richtext.facet#link` with `uri`; planning should include a dedicated transformation function (with fixtures including emoji/unicode) rather than ad hoc string replacement.

**Primary recommendation:** Plan Phase 2 around a transactional upsert pipeline keyed by Bluesky `uri`, with facet-aware text/link transformation and immediate Wagtail publish on successful import.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 6.0.3 latest (PyPI, 2026-03-03); project baseline `>=5.2.8` | Management command, ORM upserts, transactions | Existing application/runtime foundation; no new framework needed. |
| Wagtail | 7.3.1 latest (PyPI, 2026-03-03); project baseline `>=7.2.3` | `MicroPostPage` creation/update/publish | Destination content model already exists in `apps/content/models.py`. |
| httpx | 0.28.1 latest (PyPI, 2024-12-06); already in project | Bluesky XRPC client for `listRecords` and identity lookups | Already used for external sync integrations (`apps/gadgets/sync.py`). |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ATProto lexicon endpoints | Current public lexicons (GitHub main, fetched 2026-03-19) | Canonical contracts for record payload shape and facets | Use as source-of-truth for field mapping and parser behavior. |
| Django test framework (`manage.py test`) | Project default | Contract tests for deterministic import, dedupe, and render mapping | Use for all phase verification; matches current repo test style. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw `httpx` + lexicon-defined payload handling | `atproto` SDK | SDK remains pre-1.0 and adds dependency churn for a narrow import path. |
| Unique key on source `uri` | Heuristic dedupe by text + date | Heuristic matching causes false duplicates/collisions; not deterministic. |
| Facet-aware link rendering | Regex URL replacement only | Misses canonical URIs and fails on unicode byte offset edge cases. |

**Installation:**
```bash
# No new dependency required for Phase 2.
# Reuse existing Django + Wagtail + httpx stack.
```

**Version verification:** versions/publish dates verified on 2026-03-19 via PyPI JSON API (`Django`, `wagtail`, `httpx`).

## Architecture Patterns

### Recommended Project Structure
```text
apps/
└── bluesky/
    ├── client.py                          # listRecords pagination + normalization
    ├── reconcile.py                       # create/update/no-op decision set
    ├── publish.py                         # MicroPostPage create/update + publish
    ├── sync.py                            # single orchestration entrypoint
    ├── management/commands/sync_bluesky.py# manual trigger
    ├── models.py                          # source post mapping + sync metadata
    └── tests/
        ├── test_sync_bluesky_command.py
        ├── test_reconcile.py
        ├── test_publish.py
        └── test_transform.py
```

### Pattern 1: URI-Keyed Idempotent Upsert
**What:** Store a mapping row per source post keyed by Bluesky record URI; update existing records instead of creating duplicates.
**When to use:** Every import pass (including reruns of the same source window).
**Example:**
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json
# listRecords returns per-record: uri, cid, value
mapping, created = BlueskyPostMap.objects.update_or_create(
    source_uri=record["uri"],
    defaults={
        "source_cid": record["cid"],
        "source_did": source.did,
    },
)
```

### Pattern 2: Facet-Aware Text/Link Transform
**What:** Render post text plus links from `facets` (`app.bsky.richtext.facet#link`), respecting UTF-8 byte indexing.
**When to use:** Building `MicroPostPage.body` value from Bluesky record payload.
**Example:**
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/richtext/facet.json
# byteSlice uses UTF-8 byteStart/byteEnd offsets
for facet in facets:
    for feature in facet.get("features", []):
        if feature.get("$type") == "app.bsky.richtext.facet#link":
            uri = feature.get("uri")
            # map facet span -> anchor tag using canonical uri
```

### Pattern 3: Explicit Auto-Publish Mutation Boundary
**What:** Create/update `MicroPostPage` under `BlogIndexPage`, then publish via Wagtail revision API.
**When to use:** After a source post is accepted as create/update operation.
**Example:**
```python
# Source: apps/content/management/commands/bootstrap_content.py
blog_index.add_child(instance=micropost)
micropost.save()
micropost.save_revision().publish()
```

### Anti-Patterns to Avoid
- **Text/date dedupe keys:** never use content heuristics as identity; use source URI/DID+rkey.
- **Create-only import loop:** reruns must be upsert/no-op capable.
- **Regex-only link parsing:** ignores canonical facet links and byte-index rules.
- **Split logic across command/task/admin:** keep one sync service path and multiple thin triggers.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Source record identity | Custom hash from text+timestamp | Bluesky record `uri` from `listRecords` | Official durable per-record identifier for deterministic dedupe. |
| Link semantics | Homemade parser that ignores facets | `app.bsky.richtext.facet` link features | Official source includes canonical link targets and indexing semantics. |
| Publish state machine | Manual field toggling of `live` flags | Wagtail revision publish API (`save_revision().publish()`) | Keeps Wagtail revision/history semantics correct. |
| Manual sync wiring | Ad hoc scripts | Django management command + service function | Matches existing operational flow and testability patterns in repo. |

**Key insight:** Determinism comes from trusted source identity + transactional upsert + one orchestration path; hand-rolled shortcuts usually break one of those three.

## Common Pitfalls

### Pitfall 1: Duplicate imports on rerun
**What goes wrong:** Re-running manual sync creates a second `MicroPostPage` for the same Bluesky post.
**Why it happens:** Import path uses create-only writes or heuristic matching.
**How to avoid:** Add DB uniqueness on source post key and perform upsert inside transaction.
**Warning signs:** Imported count increases when no source data changed.

### Pitfall 2: Broken/missing links in rendered microblog
**What goes wrong:** Links differ from Bluesky rendering or disappear.
**Why it happens:** Parser ignores `facets` and only uses raw text URL detection.
**How to avoid:** Prefer facet links and validate transform with unicode fixtures.
**Warning signs:** Emoji-heavy posts or punctuated URLs render incorrectly.

### Pitfall 3: Content is imported but not published
**What goes wrong:** Entries exist in CMS tree but never appear in live feed.
**Why it happens:** Save occurs without revision publish call.
**How to avoid:** Enforce publish step in importer mutation function and test `live=True` result.
**Warning signs:** Admin shows pages with unpublished state after sync success.

### Pitfall 4: Drift between entry points
**What goes wrong:** CLI/manual behavior differs from future scheduled behavior.
**Why it happens:** Business logic duplicated in management command/task/admin.
**How to avoid:** One `run_sync()` service called by all triggers.
**Warning signs:** Different result counters for same source window.

## Code Examples

Verified patterns from official sources and current repo:

### Fetch records deterministically
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json
response = httpx.get(
    "https://public.api.bsky.app/xrpc/com.atproto.repo.listRecords",
    params={
        "repo": source.did,
        "collection": "app.bsky.feed.post",
        "limit": 100,
        "cursor": cursor,
    },
    timeout=30,
)
payload = response.json()  # records[].uri, records[].cid, records[].value
```

### Preserve canonical links from facets
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/richtext/facet.json
if feature.get("$type") == "app.bsky.richtext.facet#link":
    canonical_uri = feature["uri"]
```

### Auto-publish imported page
```python
# Source: apps/content/management/commands/bootstrap_content.py
parent.add_child(instance=micropost_page)
micropost_page.save()
micropost_page.save_revision().publish()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dedupe by text/timestamp similarity | Dedupe by durable source record identity (`uri` / DID+rkey) | Established ATProto repo model and v1 reliability goals | Safe reruns and replayable imports. |
| URL parsing from plain text only | Facet-aware link extraction with canonical `uri` | Richtext facet model adoption in Bluesky APIs | Accurate link preservation and fewer render mismatches. |
| Save-only CMS writes | Revision-based publish call during import | Existing Wagtail patterns in repo and docs | Meets auto-publish requirement predictably. |

**Deprecated/outdated:**
- `app.bsky.feed.post.entities` is deprecated in lexicon; use `facets` for link handling.

## Open Questions

1. **Where should source post mapping live for v1?**
   - What we know: deterministic dedupe requires persisted source key and cid.
   - What's unclear: exact model split (`BlueskyPostMap` only vs fields on source settings model).
   - Recommendation: dedicated mapping model in `apps/bluesky/models.py` with unique index on source URI.

2. **How rich should v1 link rendering be?**
   - What we know: requirement is link preservation, not full mention/tag parity.
   - What's unclear: whether to support mention/tag decorations now.
   - Recommendation: implement only text + link facets in Phase 2; defer mention/tag rendering unless needed for acceptance.

3. **What is canonical parent for imported microposts?**
   - What we know: `MicroPostPage.parent_page_types` restricts parent to `BlogIndexPage`.
   - What's unclear: whether to use first live blog index or configured target page.
   - Recommendation: explicit deterministic selector (single configured target, fallback to first live blog index with hard failure if missing).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django `manage.py test` (unittest style) |
| Config file | none (`pytest.ini` not present) |
| Quick run command | `make test ARGS='apps.bluesky.tests'` |
| Full suite command | `make test` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SYNC-02 | Manual command imports new Bluesky posts into microblog entries | integration | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` | ❌ Wave 0 |
| SYNC-04 | Re-running same source records is idempotent (no duplicate pages) | unit + integration | `make test ARGS='apps.bluesky.tests.test_reconcile apps.bluesky.tests.test_publish'` | ❌ Wave 0 |
| PUBL-01 | Imported text matches source post text in rendered body contract | unit | `make test ARGS='apps.bluesky.tests.test_transform'` | ❌ Wave 0 |
| PUBL-02 | Imported links preserve canonical Bluesky link targets | unit | `make test ARGS='apps.bluesky.tests.test_transform'` | ❌ Wave 0 |
| PUBL-03 | Imported entries are published immediately after import | integration | `make test ARGS='apps.bluesky.tests.test_publish'` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `make test ARGS='apps.bluesky.tests.test_reconcile apps.bluesky.tests.test_transform'`
- **Per wave merge:** `make test ARGS='apps.bluesky.tests'`
- **Phase gate:** `make test`

### Wave 0 Gaps
- [ ] `apps/bluesky/tests/test_sync_bluesky_command.py` - manual trigger contract for `SYNC-02`
- [ ] `apps/bluesky/tests/test_reconcile.py` - idempotent diff/upsert behavior for `SYNC-04`
- [ ] `apps/bluesky/tests/test_publish.py` - Wagtail publish + dedupe persistence for `SYNC-04`, `PUBL-03`
- [ ] `apps/bluesky/tests/test_transform.py` - text + link facet fidelity for `PUBL-01`, `PUBL-02`
- [ ] `apps/bluesky/client.py`, `apps/bluesky/reconcile.py`, `apps/bluesky/publish.py`, `apps/bluesky/sync.py` - production code modules currently absent

## Sources

### Primary (HIGH confidence)
- `.planning/REQUIREMENTS.md` - authoritative IDs and acceptance scope for this phase
- `.planning/ROADMAP.md` - phase goal, dependencies, and success criteria
- `.planning/PROJECT.md` - milestone constraints and out-of-scope boundaries
- `apps/content/models.py` - `MicroPostPage` schema and parent restrictions
- `apps/content/management/commands/bootstrap_content.py` - in-repo Wagtail publish pattern (`save_revision().publish()`)
- `apps/gadgets/sync.py` and `apps/gadgets/management/commands/sync_gadgets.py` - established sync orchestration and command pattern
- `https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json` - record identity/pagination contract
- `https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/feed/post.json` - post text/facets schema and deprecated fields
- `https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/app/bsky/richtext/facet.json` - UTF-8 byte indexing and link facet schema
- `https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/identity/resolveHandle.json` - handle->DID contract
- `https://atproto.com/specs/at-uri-scheme` - durability guidance for DID vs handle URIs
- PyPI JSON APIs:
  - `https://pypi.org/pypi/Django/json`
  - `https://pypi.org/pypi/wagtail/json`
  - `https://pypi.org/pypi/httpx/json`

### Secondary (MEDIUM confidence)
- `https://docs.bsky.app/docs/advanced-guides/post-richtext` - explanatory facet handling guidance and indexing caveats
- `https://docs.bsky.app/docs/api/com-atproto-repo-list-records` - API endpoint overview text

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - grounded in existing repo dependencies plus verified current package metadata
- Architecture: HIGH - aligns with working in-repo sync patterns and official Bluesky record contracts
- Pitfalls: HIGH - directly tied to requirement failure modes and official facet/identity specs

**Research date:** 2026-03-19
**Valid until:** 2026-04-18
