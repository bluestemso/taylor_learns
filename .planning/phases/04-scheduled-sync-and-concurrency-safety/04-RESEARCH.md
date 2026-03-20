# Phase 4: Scheduled Sync and Concurrency Safety - Research

**Researched:** 2026-03-20
**Domain:** Celery-beat scheduled execution and single-flight sync safety for Bluesky import
**Confidence:** HIGH

## User Constraints

`CONTEXT.md` is not present for this phase, so roadmap + requirements are the only hard constraints.

### Locked Decisions
- Implement Phase 4 only: scheduled sync + overlap prevention.
- Must satisfy requirement IDs: SYNC-03, LIFE-04.
- Preserve Phase 3 behavior and counters (`imported/updated/removed/skipped/failed`) and reuse the same `run_sync` pipeline.
- Use existing project stack (Django + Celery + django-celery-beat + Redis/Postgres), not a new scheduler platform.

### Claude's Discretion
- Exact lock mechanism implementation (DB lease lock vs cache lock) as long as overlap prevention is deterministic.
- Scheduling cadence defaults and enable/disable control shape.
- Where to surface scheduled/overlap outcomes in operator visibility.

### Deferred Ideas (OUT OF SCOPE)
- Firehose/realtime ingestion.
- Multi-account sync orchestration.
- Media import/thread/quote relationship work.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SYNC-03 | User can schedule recurring polling sync runs without manual intervention. | Reuse existing Celery + `django-celery-beat` bootstrap flow (`SCHEDULED_TASKS` + `bootstrap_celery_tasks`) and add a Bluesky periodic task that calls the same orchestration path used by manual sync. |
| LIFE-04 | User can rely on the system to prevent overlapping sync runs for the same source account. | Add single-flight source lock (recommended: DB lease lock with compare-and-set update) around `run_sync`, with explicit overlap-skip outcome and lock release in `finally`. |
</phase_requirements>

## Summary

The codebase is already positioned for scheduled execution: Celery is configured, `django_celery_beat` is installed, schedule materialization already exists via `apps/web/management/commands/bootstrap_celery_tasks.py`, and there is a proven task pattern in `apps/gadgets/tasks.py`. Phase 4 should not introduce a new execution system; it should add a Bluesky task entrypoint and wire it into existing `SCHEDULED_TASKS`.

Concurrency safety is currently missing in `apps/bluesky/sync.py`: manual command and future scheduled task would both call `run_sync()` with no lock boundary. Celery docs explicitly note periodic tasks may overlap if runtime exceeds schedule interval, and recommend a lock strategy. The Phase 4 design must therefore make `run_sync` single-flight per source.

Primary implementation recommendation: use a source-scoped DB lease lock (atomic compare-and-set update on source lock fields) that is acquired before external API/page mutations, released in `finally`, and treated as a deterministic overlap skip when not acquired. This avoids dependence on cache backend atomic guarantees in DEBUG environments and keeps correctness in the same durability layer as sync metadata.

**Primary recommendation:** Implement scheduled sync as a Celery periodic task that calls `run_sync`, and enforce LIFE-04 with a per-source DB lease lock in `run_sync` so manual and scheduled triggers share one safe single-flight path.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 6.0.3 (locked in `uv.lock`) | ORM transactions, atomic updates, management commands | Existing sync orchestration and admin visibility are Django-native. |
| Celery | 5.6.2 (locked in `uv.lock`) | Background task execution for scheduled sync | Already configured in project (`taylor_learns/celery.py`, docker `celery` service). |
| django-celery-beat | 2.9.0 (locked in `uv.lock`) | DB-backed periodic scheduling | Already configured (`CELERY_BEAT_SCHEDULER`) and bootstrapped by existing command. |
| Redis (redis-py client) | redis 6.4.0 locked (PyPI latest 7.3.0) | Celery broker/result backend, optional lock backend | Existing infra; no new runtime needed for scheduling. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Wagtail | 7.3.1 (locked in `uv.lock`) | Publish/unpublish lifecycle target for sync side effects | Existing run_sync import/update/remove behavior must remain unchanged for scheduled runs. |
| Django cache framework (`cache.add`) | Django 6.0 API | Optional distributed lock primitive | Use only if adopting cache lock approach with guaranteed atomic backend configuration. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| DB lease lock on source row | Redis/cache lock via `cache.add` | Cache lock is simpler but backend atomicity/configuration is environment-sensitive; DB lease lock is stronger by default in this repo. |
| Existing Celery beat + bootstrap command | OS cron / external scheduler | Adds operational surface and duplicates existing project scheduler path. |
| Single orchestration path (`run_sync`) for manual + scheduled | Separate scheduled-specific sync logic | Increases behavior drift risk and can break criterion "scheduled equals manual outcomes". |

**Installation:**
```bash
# No new dependency required for Phase 4.
```

**Version verification:**
- Verified via lockfile and PyPI metadata on 2026-03-20:
  - `django` 6.0.3 (uploaded 2026-03-03)
  - `celery` 5.6.2 (uploaded 2026-01-04)
  - `django-celery-beat` 2.9.0 (uploaded 2026-02-28)
  - `wagtail` 7.3.1 (uploaded 2026-03-03)
  - `httpx` 0.28.1 (uploaded 2024-12-06)

## Architecture Patterns

### Recommended Project Structure
```
apps/bluesky/
|-- sync.py                         # add lock acquire/release boundary around existing orchestration
|-- tasks.py                        # new Celery task entrypoint for scheduled run
|-- management/commands/sync_bluesky.py  # existing manual path remains
|-- tests/
|   |-- test_scheduled_sync.py      # new schedule/task contract tests
|   `-- test_sync_concurrency.py    # new overlap prevention tests
taylor_learns/
`-- settings.py                     # add BLUESKY schedule + enable flag in SCHEDULED_TASKS
```

### Pattern 1: Trigger/worker parity (single orchestration path)
**What:** Manual command and Celery task both call the same `run_sync()` service.
**When to use:** Any sync domain where behavior parity between trigger types is required.
**Example:**
```python
# Source: project pattern in apps/gadgets/tasks.py + apps/bluesky/management/commands/sync_bluesky.py
@shared_task
def sync_bluesky_task(limit: int = 100):
    return run_sync(limit=limit)

# management command continues to call run_sync(limit=...)
```

### Pattern 2: Per-source single-flight lease lock
**What:** Acquire a source-scoped lease atomically; skip if already held and unexpired.
**When to use:** Scheduled + manual triggers can fire concurrently.
**Example:**
```python
# Source: Django QuerySet.update contract + existing BlueskySourceSettings model usage
with transaction.atomic():
    acquired = BlueskySourceSettings.objects.filter(id=source_settings.id).filter(
        Q(sync_lock_expires_at__isnull=True) | Q(sync_lock_expires_at__lt=now)
    ).update(sync_lock_token=token, sync_lock_expires_at=lease_until)

if acquired == 0:
    return {"imported": 0, "updated": 0, "removed": 0, "skipped": 0, "failed": 0, "overlap_skipped": 1}
```

### Pattern 3: Schedule as configuration, not code branching
**What:** Register Bluesky periodic task in `SCHEDULED_TASKS` and materialize via existing bootstrap command.
**When to use:** Keep ops flow consistent with existing scheduled gadgets sync.
**Example:**
```python
# Source: taylor_learns/settings.py + apps/web/management/commands/bootstrap_celery_tasks.py
SCHEDULED_TASKS["bluesky-sync"] = {
    "task": "apps.bluesky.tasks.sync_bluesky_task",
    "schedule": schedules.crontab(minute="*/15"),
    "enabled": BLUESKY_SYNC_ENABLED,
}
```

### Anti-Patterns to Avoid
- **Dual logic paths:** Implementing scheduled sync logic separate from `run_sync` risks lifecycle drift.
- **Long DB transaction wrapping whole sync:** Keep lock acquisition atomic and short; do not hold open transaction across network pagination.
- **Non-expiring lock state:** Missing lease timeout can permanently deadlock sync after worker crash.
- **Assuming beat serialization is enough:** Celery docs state periodic tasks may overlap; explicit lock is still required.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scheduling runtime | New cron/service framework | Existing Celery + `django-celery-beat` + `SCHEDULED_TASKS` bootstrap flow | Already deployed pattern in this project; fewer moving pieces. |
| Trigger-specific sync behavior | Separate scheduled-sync orchestrator | Reuse `run_sync` from both task and command | Guarantees scheduled outcomes match manual outcomes. |
| Concurrency handling | "Best effort" timestamp checks without atomic boundary | Atomic lock acquire/release (DB lease lock recommended) | Prevents race windows where two workers both proceed. |

**Key insight:** Phase 4 is operational hardening, not a new import algorithm; preserve Phase 3 semantics and add scheduling + single-flight guarantees around the existing pipeline.

## Common Pitfalls

### Pitfall 1: Overlap from cadence < execution time
**What goes wrong:** Beat enqueues a second task while first sync is still running.
**Why it happens:** Periodic scheduling does not serialize task execution by itself.
**How to avoid:** Enforce per-source lock in `run_sync` and record overlap skip outcome.
**Warning signs:** Two overlapping run start timestamps, doubled API traffic, unexpected counter spikes.

### Pitfall 2: Lock never released after crash
**What goes wrong:** All future syncs skipped indefinitely.
**Why it happens:** Lock without lease expiration or owner token-safe release.
**How to avoid:** Use lease timeout + token-based release (`release only if token matches`).
**Warning signs:** Repeated overlap skips with no active worker.

### Pitfall 3: Scheduled path drifts from manual semantics
**What goes wrong:** Scheduled runs import/update/remove differently than command runs.
**Why it happens:** Task path bypasses `run_sync` or mutates counters/output contract.
**How to avoid:** Call `run_sync` directly from task and keep one source of truth for counters.
**Warning signs:** Command output and scheduled run records disagree for same payloads.

### Pitfall 4: Cache lock chosen but backend is non-atomic in dev/test
**What goes wrong:** False confidence in overlap prevention during local/test validation.
**Why it happens:** Default cache is `DummyCache` in DEBUG in this project.
**How to avoid:** Prefer DB lock, or configure dedicated Redis lock cache alias explicitly for lock path.
**Warning signs:** Lock acquisition always reports success in DEBUG regardless of concurrent runs.

## Code Examples

Verified patterns from official docs and current code:

### Celery periodic tasks may overlap (requires lock strategy)
```text
# Source: Celery periodic tasks docs
"Like with cron, the tasks may overlap if the first task doesn't complete
before the next. If that's a concern you should use a locking strategy..."
```

### Existing scheduled task bootstrap pattern in this repo
```python
# Source: apps/web/management/commands/bootstrap_celery_tasks.py
for task_name, task_config in settings.SCHEDULED_TASKS.items():
    schedule_spec = task_config.pop("schedule")
    schedule, field = ModelEntry.to_model_schedule(schedule_spec)
    task_config[field] = schedule
    PeriodicTask.objects.update_or_create(name=task_name, defaults=task_config)
```

### Existing manual sync contract to preserve
```python
# Source: apps/bluesky/management/commands/sync_bluesky.py
result = run_sync(limit=int(options.get("limit") or 100))
self.stdout.write(
    f"Sync complete: imported={result['imported']} updated={result['updated']} "
    f"removed={result['removed']} skipped={result['skipped']} failed={result['failed']}"
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual-only sync invocation | Manual + periodic task invoking one orchestrator | Phase 4 target | Reliability without operator intervention. |
| No explicit overlap control | Per-source single-flight lock with deterministic skip | Phase 4 target | Prevents concurrent writes/race outcomes. |
| Implicit scheduler assumptions | Explicit lock because periodic tasks can overlap | Celery guidance current in 5.6 docs | Aligns implementation with documented behavior. |

**Deprecated/outdated:**
- Relying on beat cadence alone for mutual exclusion.
- Adding a new scheduler platform when django-celery-beat is already active.

## Open Questions

1. **What default cadence should be shipped (`*/15`, hourly, etc.)?**
   - What we know: Existing gadgets schedule is hourly (`minute=0`), but Bluesky freshness may need higher cadence.
   - What's unclear: Desired freshness vs API cost budget for production.
   - Recommendation: Start with `*/15` behind `BLUESKY_SYNC_ENABLED=false` default; tune after observing run duration and API usage.

2. **Should overlap skips be persisted as run rows or only logged?**
   - What we know: Current run visibility model records completed runs with counters.
   - What's unclear: Whether operator wants explicit "skipped_due_to_overlap" history.
   - Recommendation: Persist a run row with zero counters + `overlap_skipped` marker (or explicit status field) for auditability.

3. **Lock placement: in task wrapper or inside `run_sync`?**
   - What we know: Both manual and scheduled triggers must honor LIFE-04.
   - What's unclear: None technically; this is a design choice.
   - Recommendation: Place lock inside `run_sync` so all trigger paths inherit safety automatically.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Django test runner (`python manage.py test`) |
| Config file | none (default Django test discovery) |
| Quick run command | `make test ARGS='apps.bluesky.tests.test_scheduled_sync apps.bluesky.tests.test_sync_concurrency'` |
| Full suite command | `make test` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SYNC-03 | Periodic task executes sync without manual command and reuses `run_sync` path | unit/integration | `make test ARGS='apps.bluesky.tests.test_scheduled_sync'` | ❌ Wave 0 |
| LIFE-04 | Overlapping manual/scheduled runs for same source do not execute concurrently | integration/concurrency | `make test ARGS='apps.bluesky.tests.test_sync_concurrency'` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `make test ARGS='apps.bluesky.tests.test_scheduled_sync apps.bluesky.tests.test_sync_concurrency'`
- **Per wave merge:** `make test ARGS='apps.bluesky.tests'`
- **Phase gate:** `make test`

### Wave 0 Gaps
- [ ] `apps/bluesky/tasks.py` tests (`apps/bluesky/tests/test_scheduled_sync.py`) for enabled/disabled task behavior and `run_sync` parity.
- [ ] Concurrency tests (`apps/bluesky/tests/test_sync_concurrency.py`) covering second-run overlap skip and lock release on failure.
- [ ] If lock metadata fields/model are added, migration contract tests for uniqueness/lease semantics.

## Sources

### Primary (HIGH confidence)
- Repository code inspected:
  - `apps/bluesky/sync.py`
  - `apps/bluesky/management/commands/sync_bluesky.py`
  - `apps/bluesky/models.py`
  - `apps/web/management/commands/bootstrap_celery_tasks.py`
  - `taylor_learns/settings.py`
  - `apps/gadgets/tasks.py`
  - `docker-compose.yml`
- Celery periodic tasks docs (overlap warning + locking guidance): https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
- Celery task cookbook lock example: https://docs.celeryq.dev/en/stable/tutorials/task-cookbook.html
- Django transactions docs (`atomic`, transaction duration guidance): https://docs.djangoproject.com/en/stable/topics/db/transactions/
- Django cache API (`cache.add` semantics): https://docs.djangoproject.com/en/stable/topics/cache/
- django-celery-beat docs (DB scheduler behavior/timezone warning): https://django-celery-beat.readthedocs.io/en/latest/

### Secondary (MEDIUM confidence)
- PostgreSQL advisory lock reference (considered alternative lock approach): https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - grounded in lockfile versions and already-installed project components.
- Architecture: HIGH - derived from existing code boundaries and official Celery overlap guidance.
- Pitfalls: HIGH - directly tied to current settings/runtime behavior (`DEBUG` cache mode, no current sync lock).

**Research date:** 2026-03-20
**Valid until:** 2026-04-19
