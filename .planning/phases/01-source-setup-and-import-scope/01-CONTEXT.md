# Phase 1: Source Setup and Import Scope - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Configure one authorized Bluesky source and define the historical import boundary for this milestone. This phase covers setup and visibility of the active configuration only; import execution behavior is handled in later phases.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<specifics>
## Specific Ideas

- Keep this phase operationally consistent with existing admin-first sync workflows already used for gadgets.
- Favor clarity over flexibility for first milestone setup (single source, explicit verification, explicit backfill boundary).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and milestones
- `.planning/ROADMAP.md` — Phase 1 boundary, requirements mapping, and success criteria.
- `.planning/PROJECT.md` — Milestone constraints and locked product-level decisions.
- `.planning/REQUIREMENTS.md` — Authoritative requirement IDs for this phase (`SYNC-01`, `SYNC-05`).

### Research guidance for this milestone
- `.planning/research/SUMMARY.md` — Consolidated guidance and risk framing for Bluesky integration.
- `.planning/research/STACK.md` — Stack-level recommendations and constraints for Bluesky sync.
- `.planning/research/ARCHITECTURE.md` — Integration boundaries and component expectations.
- `.planning/research/PITFALLS.md` — High-risk mistakes and prevention guidance relevant to setup choices.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/gadgets/admin.py`: Existing admin sync controls, list display patterns, and "sync now" action style are reusable for source configuration UX.
- `apps/gadgets/sync.py`: Existing sync orchestration and status-summary pattern can inform how source/backfill settings are consumed.
- `apps/gadgets/models.py`: Existing source/status model fields show a proven approach for storing sync metadata.
- `apps/gadgets/tasks.py`: Existing Celery task wrapper pattern can be mirrored when this feature reaches execution phases.
- `apps/web/management/commands/bootstrap_celery_tasks.py`: Existing task bootstrap flow defines how scheduled jobs are managed from config.

### Established Patterns
- App-domain organization pattern (`apps/<domain>/models.py`, `admin.py`, `tasks.py`, `management/commands/`) should be followed for this feature.
- Admin as operator control plane is already established for sync-driven capabilities.
- Sync status and summary bookkeeping pattern (synced/skipped/failed style counters) is established and should stay consistent across integrations.

### Integration Points
- `taylor_learns/settings.py`: Existing `SCHEDULED_TASKS` pattern is the expected integration point for recurring sync wiring in later phases.
- `apps/content/models.py`: `MicroPostPage` is the destination content type and should remain the downstream target for import pipeline phases.
- `apps/gadgets/*`: Current sync implementation provides the closest in-repo reference for source configuration and operational UX.

</code_context>

<deferred>
## Deferred Ideas

- Source configuration change history/audit log (defer to a later phase if operational need emerges).
- Media import and post-relationship modeling remain deferred per milestone plan.

</deferred>

---

*Phase: 01-source-setup-and-import-scope*
*Context gathered: 2026-03-19*
