---
phase: 03
slug: post-lifecycle-reconciliation-and-run-visibility
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django test runner (`manage.py test`) |
| **Config file** | none (uses Django settings/test discovery) |
| **Quick run command** | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'`
- **After every plan wave:** Run `make test ARGS='apps.bluesky.tests'`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | LIFE-01 | unit/integration | `make test ARGS='apps.bluesky.tests.test_publish apps.bluesky.tests.test_sync_bluesky_command'` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | LIFE-02 | integration | `MISSING — Wave 0 must create apps/bluesky/tests/test_sync_lifecycle_reconciliation.py first` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | LIFE-03 | unit/integration | `MISSING — Wave 0 must create apps/bluesky/tests/test_sync_run_visibility.py first` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | LIFE-03 | integration | `make test ARGS='apps.bluesky.tests.test_sync_bluesky_command'` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/bluesky/tests/test_sync_lifecycle_reconciliation.py` — deletion reconciliation and removed counter scenarios
- [ ] `apps/bluesky/tests/test_sync_run_visibility.py` — persisted run summary/admin visibility assertions
- [ ] `apps/bluesky/tests/test_sync_bluesky_command.py` updates — include `removed` in rendered command summary

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
