# Unit 00: Project Scaffold

## Goal

Produce a runnable FastAPI application skeleton: app factory, configuration,
static file serving, a base template shell that loads HTMX and the CSS, an
empty dashboard route, and a pytest + httpx test harness with one smoke test.

## Design

Minimal by intent — this unit is a shell, not a feature. The page shows a
plain "No items yet" placeholder. Styling is limited to a CSS reset; all
visual tokens arrive in Unit 12. HTMX is vendored as a local static file so
the app runs offline with no CDN dependency.

## Implementation

### Project layout
Create the folders from `architecture.md`: `app/`, `app/routers/`,
`app/templates/partials/`, `app/static/css/`, `app/static/js/`, `tests/`,
`data/`.

### app/config.py
A `Settings` dataclass with `BASE_DIR`, `DB_PATH` (default
`data/household.db`), `POLL_INTERVAL_S = 10`, and the food thresholds
(`EAT_SOON_DAYS = 3`, `PURGE_AFTER_DAYS = 7`).

### app/main.py
`create_app()` factory: create the FastAPI instance, include the dashboard
router, mount `/static`, and create the `data/` directory if missing.
Export a module-level `app = create_app()` so `uvicorn app.main:app` works.

### app/routers/dashboard.py
A single `GET /` that renders `dashboard.html` with an empty context.

### Templates
- `base.html` — full HTML shell with `<head>` linking
  `/static/css/styles.css` and `<script src="/static/js/htmx.min.js" defer>`.
- `dashboard.html` — extends `base.html`; contains a dashboard container and
  an empty-state message.

### Static assets
- `styles.css` — CSS reset only.
- `htmx.min.js` — vendored HTMX (latest stable), no CDN.

### Tests
- `tests/conftest.py` — `TestClient` fixture wired to `create_app()` with a
  temporary database path.
- `tests/test_smoke.py` — `GET /` returns 200 and contains the page shell.

### requirements.txt
Pin the runtime + dev dependencies listed below.

## Dependencies

- `fastapi` (framework)
- `uvicorn[standard]` (ASGI server)
- `jinja2` (templating)
- `pytest` (tests)
- `httpx` (TestClient transport)

## Verify when done

- [ ] `uvicorn app.main:app --reload` serves the dashboard with no errors
- [ ] The page loads HTMX and the stylesheet (check DevTools Network)
- [ ] `pytest` passes the smoke test
- [ ] No browser console errors
