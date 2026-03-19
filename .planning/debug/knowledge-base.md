# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## bluesky-admin-source-settings-500 — Admin source settings page returned HTTP 500 due to missing table
- **Date:** 2026-03-19
- **Error patterns:** admin changelist, HTTP 500, ProgrammingError, relation does not exist, bluesky_blueskysourcesettings, unapplied migrations, bluesky
- **Root cause:** Bluesky migrations that create `bluesky_blueskysourcesettings` were present but unapplied in the running database.
- **Fix:** Applied pending bluesky migrations to create required tables (`bluesky_blueskysourcesettings`, `bluesky_blueskypostmap`) in the local database.
- **Files changed:** none
---
