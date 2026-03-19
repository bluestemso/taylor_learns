# Requirements: Taylor Learns

**Defined:** 2026-03-19
**Core Value:** Publish in one place and reliably syndicate personal writing/activity so the site remains the canonical home for content.
**Milestone:** v1.0 Bluesky Microblog Import

## v1 Requirements

Requirements committed for this milestone.

### Ingestion

- [ ] **SYNC-01**: User can connect exactly one owner Bluesky account as the import source for this milestone.
- [ ] **SYNC-02**: User can run a manual sync that imports new Bluesky posts into microblog entries.
- [ ] **SYNC-03**: User can schedule recurring polling sync runs without manual intervention.
- [ ] **SYNC-04**: User can re-run sync safely without creating duplicate microblog entries.
- [ ] **SYNC-05**: User can configure a backfill window to limit initial historical import scope.

### Lifecycle

- [ ] **LIFE-01**: User can see Bluesky post edits reflected in the corresponding microblog entry after sync.
- [ ] **LIFE-02**: User can have deleted Bluesky posts soft-removed (unpublished/marked removed) in the CMS after sync.
- [ ] **LIFE-03**: User can view sync run outcomes including counts for imported, updated, removed, and skipped posts.
- [ ] **LIFE-04**: User can rely on the system to prevent overlapping sync runs for the same source account.

### Publishing

- [ ] **PUBL-01**: User can see Bluesky post text rendered accurately in imported microblog entries.
- [ ] **PUBL-02**: User can see Bluesky links preserved in imported microblog entries.
- [ ] **PUBL-03**: User can have imported entries auto-published without manual review.

## Future Requirements

Deferred requirements acknowledged but not committed in this milestone.

### Enhancements

- **ENH-01**: User can import Bluesky images into CMS media and attach them to microblog entries.
- **ENH-02**: User can choose draft/review mode instead of auto-publish for imported entries.
- **ENH-03**: User can preserve reply-thread relationships between mirrored posts.
- **ENH-04**: User can preserve quote-post relationships and references.
- **ENH-05**: User can mirror multiple Bluesky accounts with account-specific policies.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Firehose/real-time ingestion | Polling + manual sync meets milestone reliability goals with lower operational complexity |
| Bidirectional publishing back to Bluesky | Milestone is one-way mirroring from Bluesky to CMS |
| Full social graph import (likes/reposts/follows) | Not necessary for validating core publishing value |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SYNC-01 | TBD | Pending |
| SYNC-02 | TBD | Pending |
| SYNC-03 | TBD | Pending |
| SYNC-04 | TBD | Pending |
| SYNC-05 | TBD | Pending |
| LIFE-01 | TBD | Pending |
| LIFE-02 | TBD | Pending |
| LIFE-03 | TBD | Pending |
| LIFE-04 | TBD | Pending |
| PUBL-01 | TBD | Pending |
| PUBL-02 | TBD | Pending |
| PUBL-03 | TBD | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 0
- Unmapped: 12 ⚠️

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after milestone v1.0 requirement scoping*
