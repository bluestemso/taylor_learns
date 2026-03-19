# Phase 1: Source Setup and Import Scope - Research

**Researched:** 2026-03-19
**Domain:** Django admin source configuration + Bluesky identity verification + import backfill boundary policy
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Setup surface
- Configuration is managed in Django admin only for this phase.
- Only superusers can change source/backfill settings.
- Setup uses a single guided edit form (not a multi-step wizard or raw-only field editing).
- Saving configuration requires successful source verification; invalid source records should not be saved.

### Source identity UX
- Operator enters the source handle; the system resolves and stores canonical identity and shows DID in UI.
- Source replacement is allowed only through an explicit replace-confirmation flow.
- Single-source constraint applies, but setup does not enforce a preconfigured expected owner identity; any verified account can be configured as the single source.
- Source details shown after setup must include handle, DID, and profile link.

### Backfill shape
- Backfill is defined as an absolute start date (not relative days or post-count).
- Backfill start date is required.
- Date boundary is interpreted at site timezone midnight.
- Backfill boundary applies to all future sync runs, not only initial import.

### Settings visibility
- Operators view settings in admin list summary plus full admin detail view.
- Summary view must show: handle, backfill date, and enabled state.
- Detail view must include an explicit read-only "effective settings" block showing what sync currently uses.
- No settings-change history is required in this phase.

### Claude's Discretion
- Exact microcopy for setup help text, warnings, and confirmation messaging.
- Exact admin field grouping/layout as long as it preserves the decisions above.
- Exact naming of the "effective settings" section.

### Deferred Ideas (OUT OF SCOPE)
- Source configuration change history/audit log (defer to a later phase if operational need emerges).
- Media import and post-relationship modeling remain deferred per milestone plan.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SYNC-01 | User can connect exactly one owner Bluesky account as the import source for this milestone. | Single-row source model + DB uniqueness guard, admin replace-confirm flow, handle->DID verification via `com.atproto.identity.resolveHandle`, superuser-only admin permissions. |
| SYNC-05 | User can configure a backfill window to limit initial historical import scope. | Required `backfill_start_date` field, site-timezone-midnight normalization, read-only effective settings rendering in admin list/detail for operator visibility. |
</phase_requirements>

## Summary

Phase 1 should be planned as a strict configuration contract, not as import logic. The repo already has a strong precedent for admin-first sync control (`apps/gadgets/admin.py`, custom changelist action template, and sync status fields), so the safest plan is to mirror that pattern with a dedicated Bluesky source configuration model and admin class. The key deliverable is a single authoritative source record with a required backfill boundary that later phases can consume deterministically.

For source identity, plan around verified DID-first storage. Official Bluesky lexicon docs for `com.atproto.identity.resolveHandle` confirm the API contract is handle input and DID output, and AT URI spec guidance warns that handle-based identifiers are non-durable. Therefore, this phase should treat handle as mutable display metadata and DID as canonical identity. This directly supports the locked decision that configuration save must fail when source verification fails.

For backfill scope, use an absolute date field and convert it to site-timezone midnight at write/read boundaries. Project settings currently use `TIME_ZONE = "UTC"`, but locked decisions require site-timezone semantics, so the model/service contract should be explicit now to prevent off-by-one behavior in later sync phases. Operator trust requirement is satisfied by exposing handle, DID, profile URL, enabled flag, and effective backfill boundary in both changelist and detail view.

**Primary recommendation:** Implement a single `BlueskySourceSettings` admin-managed model with DID-verified save validation, explicit replace-confirm flow, and required timezone-normalized backfill date exposed through an "effective settings" read-only block.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 6.0.3 latest (PyPI, 2026-03-03); project currently `>=5.2.8` | Admin UI (`ModelAdmin`), validation, permissions, model constraints | Existing app is Django-first and already runs admin as operator control plane. |
| Wagtail | 7.3.1 latest (PyPI, 2026-03-03); project currently `>=7.2.3` | Existing CMS context where sync destination lives | No new UI framework needed; this phase only configures source settings. |
| httpx | 0.28.1 latest (PyPI, 2024-12-06); already in project | Call `com.atproto.identity.resolveHandle` for source verification | Already standard in repo integrations (`apps/gadgets/sync.py`), so no new HTTP client is needed. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-celery-beat | 2.9.0 latest (PyPI, 2026-02-28) | Future consumer of configured settings via scheduled sync | Keep listed because settings created here are consumed by scheduled runs in later phases. |
| zoneinfo (stdlib) | Python 3.12+ stdlib | Convert absolute date to site-timezone midnight semantics | Required for the locked timezone-boundary decision without adding dependencies. |
| atproto (optional only) | 0.0.65 latest (PyPI, 2025-12-08) | Optional typed SDK for broader ATProto use later | Not needed for Phase 1; raw `httpx` + one endpoint is simpler and lower-risk. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Django admin guided form | Custom frontend page | Adds complexity and breaks locked "admin only" decision for this phase. |
| `httpx` direct lexicon call | `atproto` SDK | SDK is pre-1.0 and introduces churn risk for a single endpoint use case. |
| Absolute date boundary | Relative days window | Conflicts with locked decision and adds ambiguous timezone math. |

**Installation:**
```bash
# No new package required for Phase 1.
# Reuse existing Django + httpx + zoneinfo stack.
```

**Version verification:** verified current package versions and publish timestamps from official PyPI JSON APIs on 2026-03-19.

## Architecture Patterns

### Recommended Project Structure
```text
apps/
└── bluesky/
    ├── admin.py                  # guided config UI + list/detail visibility
    ├── models.py                 # single-source + backfill settings contract
    ├── forms.py                  # source verification + replace confirmation validation
    ├── services/
    │   └── identity.py           # resolve handle -> did via httpx
    └── tests/
        ├── test_admin_source_settings.py
        ├── test_identity_service.py
        └── test_settings_model.py
```

### Pattern 1: DID-Verified Save Boundary
**What:** Model/admin save path validates handle with `com.atproto.identity.resolveHandle` before persistence.
**When to use:** Every create/update of source settings in admin.
**Example:**
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/identity/resolveHandle.json
def resolve_handle_to_did(handle: str) -> str:
    response = httpx.get(
        "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle",
        params={"handle": handle},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["did"]
```

### Pattern 2: Singleton Settings with Explicit Replace Confirmation
**What:** Enforce exactly one active source row; replacements require explicit confirmation input in the form.
**When to use:** Operator attempts to swap configured source.
**Example:**
```python
# Source: https://docs.djangoproject.com/en/6.0/ref/models/constraints/
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["is_active"],
            condition=models.Q(is_active=True),
            name="unique_active_bluesky_source",
        )
    ]
```

### Pattern 3: Effective Settings Projection (Read-only)
**What:** Expose computed sync-effective values in admin detail (`handle`, `did`, `profile_url`, normalized backfill boundary, enabled state).
**When to use:** Admin detail page and summary list visibility.
**Example:**
```python
# Source: https://docs.djangoproject.com/en/6.0/ref/contrib/admin/
@admin.display(description="Effective settings")
def effective_settings(self, obj):
    return format_html(
        "Handle: {}<br>DID: {}<br>Backfill from: {} {}",
        obj.handle,
        obj.did,
        obj.backfill_start_date,
        settings.TIME_ZONE,
    )
```

### Anti-Patterns to Avoid
- **Handle as durable key:** store DID as canonical identity and handle as display-only metadata.
- **Saving before verification:** do not persist settings if handle resolution fails.
- **Implicit replacement:** require explicit replace confirmation to avoid accidental source switches.
- **Hidden effective behavior:** avoid making operators infer effective sync settings from raw fields.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Handle validity and DID mapping | Custom regex/heuristic handle checker | `com.atproto.identity.resolveHandle` endpoint | Authoritative source of truth; avoids false positives and stale assumptions. |
| Admin CRUD framework | Custom internal settings UI for this phase | Django `ModelAdmin` guided form | Locked phase decision is admin-only; repo already has proven admin patterns. |
| Timezone conversion logic | Manual offset arithmetic | `zoneinfo` + Django timezone utilities | DST/offset edge cases are easy to get wrong manually. |

**Key insight:** Phase 1 is mostly contract definition and operator UX safety; use authoritative APIs and built-in framework primitives to keep correctness high and scope tight.

## Common Pitfalls

### Pitfall 1: Source replacement without explicit operator intent
**What goes wrong:** Active source silently changes and future sync targets wrong account.
**Why it happens:** Replacement is implemented as ordinary edit with no confirmation gate.
**How to avoid:** Add explicit replace confirmation field and block save unless confirmed.
**Warning signs:** Handle/DID changes appear in DB with no explicit operator acknowledgement.

### Pitfall 2: Backfill date interpreted as naive date-time
**What goes wrong:** Later sync imports wrong day boundary by timezone offset.
**Why it happens:** Date stored/used without explicit site-timezone-midnight conversion contract.
**How to avoid:** Normalize to site timezone at midnight and display effective normalized value in admin.
**Warning signs:** Imported first post differs depending on worker timezone/environment.

### Pitfall 3: Singleton enforced only in UI
**What goes wrong:** Multiple active rows can still occur via shell/migration/race paths.
**Why it happens:** No DB-level conditional uniqueness constraint.
**How to avoid:** Add `UniqueConstraint(condition=Q(is_active=True))` and validate in form/service.
**Warning signs:** Admin list shows >1 enabled source or sync code needs arbitrary row pick.

### Pitfall 4: DID captured but not surfaced
**What goes wrong:** Operators cannot verify canonical identity and trust erodes.
**Why it happens:** DID stored internally but not shown in list/detail UI.
**How to avoid:** Include DID and profile link in required summary/detail surfaces.
**Warning signs:** Support/debug flow relies on database inspection for basic identity confirmation.

## Code Examples

Verified patterns from official sources:

### Bluesky handle resolution contract
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/identity/resolveHandle.json
# Required query param: handle
# Expected output: {"did": "did:..."}
```

### Record listing contract for later sync consumers
```python
# Source: https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json
# Required params: repo, collection
# Important defaults: limit max=100 default=50
# Returned per record: uri, cid, value
```

### AT URI durability rule
```text
# Source: https://atproto.com/specs/at-uri-scheme
Use DID-based AT URIs for durable references.
Handle-based AT URIs are not durable across handle changes.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Treat handle as primary identity | Resolve handle but persist DID as canonical identity | Codified in current AT URI and identity docs (2026 docs) | Prevents identity drift when handles change. |
| Ad hoc settings forms outside admin | Admin-centered operator control for internal workflows | Mature Django admin patterns (ongoing) | Faster delivery and lower maintenance for trusted-operator tools. |
| Relative backfill knobs (days/count) | Absolute date boundary with explicit timezone semantics | Current phase locked decision | Removes ambiguity and improves reproducibility across runs. |

**Deprecated/outdated:**
- Handle-only identity keys for durable sync mapping: replaced by DID-first identity contract.

## Open Questions

1. **What exact profile URL format should be displayed for resolved source?**
   - What we know: locked decision requires profile link in UI.
   - What's unclear: whether to prefer `https://bsky.app/profile/<handle>` display URL or DID-based URL fallback.
   - Recommendation: display handle URL first with DID fallback when handle is unavailable.

2. **Should replace confirmation be text-entry or boolean checkbox?**
   - What we know: explicit replace-confirmation flow is required.
   - What's unclear: exact UX shape is discretionary.
   - Recommendation: use explicit checkbox + changed-handle warning microcopy for simplest admin ergonomics.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django `manage.py test` (unittest-based), project on Django 5.2.x |
| Config file | none (no `pytest.ini`; defaults via Django settings) |
| Quick run command | `make test ARGS='apps.bluesky.tests.test_admin_source_settings'` |
| Full suite command | `make test` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SYNC-01 | Exactly one active source can be configured and replaced only with confirmation | unit + integration (model constraint + admin form flow) | `make test ARGS='apps.bluesky.tests.test_admin_source_settings.TestSingleSourceConstraint'` | ❌ Wave 0 |
| SYNC-05 | Required absolute backfill date stored/displayed as site-timezone-midnight effective setting | unit + integration (form validation + effective settings rendering) | `make test ARGS='apps.bluesky.tests.test_admin_source_settings.TestBackfillBoundary'` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `make test ARGS='apps.bluesky.tests.test_admin_source_settings'`
- **Per wave merge:** `make test ARGS='apps.bluesky.tests apps.gadgets.tests'`
- **Phase gate:** `make test`

### Wave 0 Gaps
- [ ] `apps/bluesky/tests/test_admin_source_settings.py` - covers SYNC-01 + SYNC-05 admin/model contract
- [ ] `apps/bluesky/tests/test_identity_service.py` - covers handle verification success/failure behavior
- [ ] `apps/bluesky/tests/test_settings_model.py` - covers uniqueness constraint and effective settings projection
- [ ] `apps/bluesky/` app skeleton + migrations - required before tests can run

## Sources

### Primary (HIGH confidence)
- `.planning/phases/01-source-setup-and-import-scope/01-CONTEXT.md` - locked implementation decisions and scope constraints
- `.planning/REQUIREMENTS.md` - authoritative requirement IDs (`SYNC-01`, `SYNC-05`)
- `apps/gadgets/admin.py` and `templates/admin/gadgets/gadgetsource/change_list.html` - existing admin-first sync UX pattern in this repo
- `apps/gadgets/models.py` - status/config model patterns already used for sync control
- `taylor_learns/settings.py` - current timezone and scheduled task wiring conventions
- https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/identity/resolveHandle.json - verified handle->DID API contract
- https://raw.githubusercontent.com/bluesky-social/atproto/main/lexicons/com/atproto/repo/listRecords.json - verified repo record listing contract
- https://atproto.com/specs/at-uri-scheme - durability guidance for DID vs handle AT URIs
- https://docs.djangoproject.com/en/6.0/ref/contrib/admin/ - `ModelAdmin` patterns for list/detail/read-only/admin actions
- https://docs.djangoproject.com/en/6.0/ref/models/constraints/ - `UniqueConstraint` semantics for singleton enforcement
- https://docs.python.org/3/library/zoneinfo.html - standard timezone handling for boundary normalization
- PyPI official JSON APIs:
  - https://pypi.org/pypi/Django/json
  - https://pypi.org/pypi/wagtail/json
  - https://pypi.org/pypi/httpx/json
  - https://pypi.org/pypi/django-celery-beat/json
  - https://pypi.org/pypi/atproto/json

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` and `.planning/research/ARCHITECTURE.md` - milestone-level stack/architecture recommendations aligned to repo patterns

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified against repo dependencies and official PyPI metadata
- Architecture: HIGH - directly constrained by locked context decisions and existing in-repo admin patterns
- Pitfalls: HIGH - grounded in official identity/URI docs plus observed sync patterns already present in repo

**Research date:** 2026-03-19
**Valid until:** 2026-04-18
