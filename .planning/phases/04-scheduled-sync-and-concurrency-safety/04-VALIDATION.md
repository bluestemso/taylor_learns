---
phase: 04
slug: scheduled-sync-and-concurrency-safety
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 04 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django test runner (`python manage.py test`) |
| **Config file** | none (default Django test discovery) |
| **Quick run command** | `make test ARGS='apps.bluesky.tests.test_scheduled_sync apps.bluesky.tests.test_sync_concurrency'` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `make test ARGS='apps.bluesky.tests.test_scheduled_sync apps.bluesky.tests.test_sync_concurrency'`
- **After every plan wave:** Run `make test ARGS='apps.bluesky.tests'`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | SYNC-03 | unit/integration | `make test ARGS='apps.bluesky.tests.test_scheduled_sync'` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | LIFE-04 | integration/concurrency | `make test ARGS='apps.bluesky.tests.test_sync_concurrency'` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/bluesky/tests/test_scheduled_sync.py` - stubs for SYNC-03
- [ ] `apps/bluesky/tests/test_sync_concurrency.py` - stubs for LIFE-04
- [ ] Existing infrastructure covers framework setup; no install work needed

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
