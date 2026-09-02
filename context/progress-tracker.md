# Progress Tracker

Update this file after every meaningful implementation
change.

## Current Phase

- Build phase 0 — Foundation (implementing the units in order)

## Current Goal

- Unit 01 — DB Plan

## Completed

- Six-file context system authored (`project-overview.md`,
  `architecture.md`, `ui-context.md`, `code-standards.md`,
  `ai-workflow-rules.md`); `AGENTS.md` aligned to the portfolio intent.
- Build plan (`context/spec/00-build-plan.md`) and all 15 unit specs authored.
- Unit 00 — Project Scaffold: `app/` skeleton, templates, vendored HTMX,
  CSS reset, pytest harness; smoke test passes.

##None — between units.

- Unit 00 — Project Scaffold (`context/spec/00-project-scaffold.md`)

## Next Up

- Unit 01 — DB Plan (`context/spec/01-db-plan.md`)
- Unit 02 — DB Implementation (`context/spec/02-db-implementation.md`)
- Unit 03 — Domain Services (`context/spec/03-domain-services.md`)

## Open Questions

- None blocking v1. Deferred: remote sync, per-medication schedules,
  Alembic migrations, data import/export.

## Architecture Decisions

- FastAPI + Uvicorn + SQLAlchemy 2.0 + SQLite + Jinja2 + HTMX + plain CSS
  (portfolio-grade, no frontend build step).
- Status is always derived, never stored; expiry purge is derived from
  `best_by_date` (deleted 7 days past best-by) — no `expired_at` column.
- `Base.metadata.create_all()` on startup for v1; Alembic as the future path.
- Single user, single machine, no auth; remote sync deferred.

## Session Notes

- Unit 00 complete. Run the app with
  `.venv\Scripts\python.exe -m uvicorn app.main:app --reload`
  (deps live in the venv; the system Python has none of them).
- Minor: starlette 1.6.0 emits a deprecation warning about `httpx` in
  TestClient (suggests `httpx2`). Harmless for now; revisit in Unit 13.
