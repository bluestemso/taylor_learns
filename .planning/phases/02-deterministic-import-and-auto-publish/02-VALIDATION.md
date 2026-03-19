---
phase: 02
slug: deterministic-import-and-auto-publish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 02 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django `manage.py test` |
| **Config file** | none - existing Django test runner |
| **Quick run command** | `make test ARGS='apps.bluesky.tests'` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `make test ARGS='apps.bluesky.tests.test_reconcile apps.bluesky.tests.test_transform'`
- **After every plan wave:** Run `make test ARGS='apps.bluesky.tests'`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | SYNC-02 | integration | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | SYNC-04 | unit + integration | `make test ARGS='apps.bluesky.tests.test_reconcile apps.bluesky.tests.test_publish'` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | PUBL-01 | unit | `make test ARGS='apps.bluesky.tests.test_transform'` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | PUBL-02 | unit | `make test ARGS='apps.bluesky.tests.test_transform'` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | PUBL-03 | integration | `make test ARGS='apps.bluesky.tests.test_publish'` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/bluesky/tests/test_sync_bluesky_command.py` - command trigger contract for `SYNC-02`
- [ ] `apps/bluesky/tests/test_reconcile.py` - idempotent reconcile behavior for `SYNC-04`
- [ ] `apps/bluesky/tests/test_publish.py` - publish + dedupe persistence for `SYNC-04`, `PUBL-03`
- [ ] `apps/bluesky/tests/test_transform.py` - text + link fidelity for `PUBL-01`, `PUBL-02`
- [ ] `apps/bluesky/client.py`, `apps/bluesky/reconcile.py`, `apps/bluesky/publish.py`, `apps/bluesky/sync.py` - production modules to implement this phase

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
