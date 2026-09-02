# Security

This is a small static demo (no accounts, no user data collected, no
backend at runtime) — see README.md's "What it does" section for exactly
what it does and doesn't track.

## Reporting an issue

If you find a security issue, please open a GitHub issue on this repo
rather than a public PR containing exploit details.

## What's in place / what to keep in place

- The TMDB API key is a build-time secret used only by the offline
  `scripts/*.py` data-prep pipeline — it is never shipped to the browser
  and never committed. Kept in a local `.env` (gitignored); `.env.example`
  shows the expected variable name only.
- Before making a repo like this public, verify no `.env` file or API key
  was ever committed: `git log --all --full-history -- .env` and a
  full-history grep for the key value should both come back empty.
- The deployed front end (`docs/`) makes no network calls at runtime beyond
  loading its own static JSON/images — no third-party scripts, no
  analytics, no tracking.
- All TMDB poster images are used under TMDB's terms for
  non-commercial/demo attribution use — see https://www.themoviedb.org/documentation/api/terms-of-use.
