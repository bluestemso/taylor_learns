# Codebase Concerns

**Analysis Date:** 2026-03-19

## Tech Debt

**Configuration Monolith:**
- Issue: Core runtime, auth, storage, CORS, Celery, Channels, AI, and logging are centralized in one large settings module, which increases merge conflicts and makes environment-specific changes risky.
- Files: `taylor_learns/settings.py`, `taylor_learns/settings_production.py`
- Impact: Small config edits can cause broad regressions; review and testing burden is high for each settings change.
- Fix approach: Split settings into domain modules (for example base/security/integrations/ai) and keep production overrides minimal.

**Gadget Sync Error Handling Is Too Broad:**
- Issue: Sync and publish paths catch broad exceptions and collapse failure modes into generic strings.
- Files: `apps/gadgets/sync.py`
- Impact: Root causes are harder to diagnose, and operational visibility is reduced when sync jobs fail.
- Fix approach: Catch expected exception classes separately, store structured failure codes, and include contextual metadata in logs.

**Mixed Sync/Async Networking in AI Tooling:**
- Issue: Async tool code performs synchronous HTTP calls.
- Files: `apps/ai/tools/weather.py`
- Impact: Event-loop blocking under load can degrade websocket responsiveness and increase tail latency.
- Fix approach: Replace sync `requests` usage with `httpx.AsyncClient` and consistent timeout/error handling.

## Known Bugs

**Weather Tool Returns Invalid Typed Payload on No Result:**
- Symptoms: Location lookups with no matches can error while constructing coordinates.
- Files: `apps/ai/tools/weather.py`
- Trigger: `get_lat_lng` returns `LatLng(lat=None, lng=None)` although model fields are typed as `float`.
- Workaround: Return explicit validation-safe sentinel values or raise a domain exception and handle it in the calling agent flow.

**Email Tool Contract Mismatch:**
- Symptoms: Tool is declared to return `bool` but returns `None`.
- Files: `apps/ai/tools/email.py`
- Trigger: `send_email` has signature `-> bool` and no explicit return statement.
- Workaround: Return `True` on success and raise on error; align function annotation with actual behavior.

## Security Considerations

**Streaming Chat Output Is Injected Without Sanitization:**
- Risk: HTML returned in token stream is inserted directly into websocket fragments before final sanitized render.
- Files: `apps/chat/consumers.py`, `templates/chat/websocket_components/system_message.html`, `templates/chat/websocket_components/final_system_message.html`, `apps/web/templatetags/markdown_tags.py`
- Current mitigation: Final message render uses sanitized markdown via `nh3`.
- Recommendations: Escape streamed chunks during incremental updates, then keep sanitized final render as the canonical output.

**Raw HTML Blocks Are Enabled in CMS Content:**
- Risk: Editor-authored raw HTML can introduce XSS or unsafe embeds if editor accounts are compromised or over-permissioned.
- Files: `apps/content/models.py`
- Current mitigation: Wagtail admin permissions limit who can edit content.
- Recommendations: Remove `RawHTMLBlock` where possible or gate usage with stricter editorial permissions and review workflows.

**Healthcheck Endpoint Bypasses Application Dependencies:**
- Risk: `/up` returns OK even when DB/Redis/Celery are degraded, creating false-positive readiness.
- Files: `apps/web/middleware/healthchecks.py`, `apps/web/views.py`
- Current mitigation: Separate token-gated health view exists in `apps/web/views.py`.
- Recommendations: Keep `/up` for liveness only and use dependency-aware checks for readiness and alerting.

## Performance Bottlenecks

**Unbounded Chat History Loading:**
- Problem: Session initialization loads full message history into memory and forwards it to LLM context.
- Files: `apps/chat/sessions.py`
- Cause: `ChatMessage.objects.filter(chat=self.chat)` is unbounded in async and sync session constructors.
- Improvement path: Cap history by token/window budget, summarize old context, and paginate long threads.

**Blocking External HTTP in Async Weather Tool:**
- Problem: Geocoding call can block worker thread in async execution paths.
- Files: `apps/ai/tools/weather.py`
- Cause: `requests.get(...)` is used inside `async def get_lat_lng`.
- Improvement path: Convert to async HTTP with explicit timeout/retry strategy.

**Large Settings Surface Slows Safe Iteration:**
- Problem: High cognitive and review overhead for every environment/config change.
- Files: `taylor_learns/settings.py`
- Cause: Single file currently contains 675 lines spanning many unrelated concerns.
- Improvement path: Modularize settings and enforce narrow ownership boundaries.

## Fragile Areas

**Gadget Deploy Swap Logic Is Filesystem-Sensitive:**
- Files: `apps/gadgets/sync.py`
- Why fragile: Publish/rollback logic uses staged/backup directory swapping without an inter-process lock; concurrent syncs can race.
- Safe modification: Add distributed or file lock around publish section and extend tests for concurrent publish attempts.
- Test coverage: `apps/gadgets/tests/` covers command wiring and visibility behavior but not concurrent publish race scenarios.

**Websocket Route Type Mismatch:**
- Files: `apps/chat/routing.py`, `apps/chat/sessions.py`
- Why fragile: Websocket route uses `<slug:chat_id>` while session logic expects integer IDs and queries DB by `id`.
- Safe modification: Use `<int:chat_id>` in websocket routes and add connection tests for malformed IDs.
- Test coverage: No websocket consumer tests detected under `apps/chat/tests/`.

## Scaling Limits

**Chat Storage and Context Growth:**
- Current capacity: Chat messages are stored indefinitely per chat and replayed into session context.
- Limit: Token/context windows and response latency degrade as `ChatMessage` volume grows.
- Scaling path: Enforce retention/summarization strategy and bound context replay in `apps/chat/sessions.py`.

**Gadget Discovery API Throughput:**
- Current capacity: Discovery paginates at 100 repos per page and loops per configured topic/owner set.
- Limit: Sync duration and GitHub API quota pressure increase with topic growth.
- Scaling path: Add conditional requests/ETags, per-run caps, and checkpointed incremental sync in `apps/gadgets/sync.py`.

## Dependencies at Risk

**Runtime-installed MCP Tooling:**
- Risk: Admin DB tool launches `uvx` with `--refresh-package`, introducing runtime variability and startup latency.
- Impact: Agent behavior can drift between runs and operational debugging is harder.
- Migration plan: Pin a vetted version without refresh in production paths, or vendor a fixed execution environment.
- Files: `apps/ai/tools/admin_db.py`

## Missing Critical Features

**No Chat/Agent Rate Limiting or Abuse Controls:**
- Problem: Realtime chat endpoints have no explicit per-user/per-IP throttling.
- Blocks: Safe cost control and predictable service quality during abusive or bursty traffic.
- Files: `apps/chat/consumers.py`, `apps/chat/routing.py`, `taylor_learns/asgi.py`

## Test Coverage Gaps

**AI and Chat Execution Paths Are Untested:**
- What's not tested: Websocket consumers, streaming flows, session lifecycle, tool execution, and failure handling.
- Files: `apps/chat/consumers.py`, `apps/chat/sessions.py`, `apps/ai/agents.py`, `apps/ai/tools/weather.py`, `apps/ai/tools/email.py`
- Risk: Regressions in authentication, streaming HTML safety, and async error handling can ship undetected.
- Priority: High

**Content and User Critical Paths Lack Focused Tests:**
- What's not tested: Wagtail content model behaviors, signup captcha/network failure paths, and profile upload validation edge cases.
- Files: `apps/content/models.py`, `apps/users/forms.py`, `apps/users/helpers.py`
- Risk: Editorial/security regressions and user-facing form failures may bypass CI.
- Priority: Medium

---

*Concerns audit: 2026-03-19*
