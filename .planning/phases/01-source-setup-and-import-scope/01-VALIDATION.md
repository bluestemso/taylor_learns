---
phase: 01
slug: source-setup-and-import-scope
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 01 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django `manage.py test` (unittest-based) |
| **Config file** | none - Django defaults |
| **Quick run command** | `make test ARGS='apps.bluesky.tests.test_admin_source_settings'` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `make test ARGS='apps.bluesky.tests.test_admin_source_settings'`
- **After every plan wave:** Run `make test ARGS='apps.bluesky.tests apps.gadgets.tests'`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SYNC-01 | unit + integration | `make test ARGS='apps.bluesky.tests.test_admin_source_settings.TestSingleSourceConstraint'` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | SYNC-05 | unit + integration | `make test ARGS='apps.bluesky.tests.test_admin_source_settings.TestBackfillBoundary'` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `apps/bluesky/tests/test_admin_source_settings.py` - stubs for SYNC-01 and SYNC-05
- [ ] `apps/bluesky/tests/test_identity_service.py` - handle verification success/failure coverage
- [ ] `apps/bluesky/tests/test_settings_model.py` - uniqueness + effective settings projection coverage
- [ ] `apps/bluesky/` app skeleton + migrations

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
