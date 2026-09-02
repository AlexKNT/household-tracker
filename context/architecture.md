# Architecture Context

## Stack

| Layer | Technology | Role |
|---|---|---|
| Web framework | FastAPI | HTTP routing, request handling, Pydantic validation |
| ASGI server | Uvicorn | Run the FastAPI app |
| ORM | SQLAlchemy 2.0 | Declarative models, queries, transactions |
| Database | SQLite | Single-file local storage (`data/household.db`) |
| Templating | Jinja2 | Server-rendered HTML fragments for HTMX |
| Interactivity | HTMX | Partial page updates + polling, no JS framework |
| Validation | Pydantic | Form/schema validation (ships with FastAPI) |
| Styling | Plain CSS | Layout, traffic-light colors, `@keyframes` flash |
| Testing | pytest + httpx | Unit tests for domain logic, endpoint tests |

Everything is standard-library-friendly on purpose. The only third-party
runtime dependencies are FastAPI, Uvicorn, SQLAlchemy, Jinja2, and HTMX
(a single JS file). No background task framework, no frontend build step.

## System Boundaries

```
household-tracker/
├── app/
│   ├── main.py            # App factory, route registration, static mount
│   ├── config.py          # Settings (DB path, thresholds, polling interval)
│   ├── db.py              # Engine, session factory, Base
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic schemas for forms
│   ├── crud.py            # Data access: queries and mutations
│   ├── services.py        # Domain logic: status derivation, expiry math
│   ├── routers/
│   │   ├── dashboard.py   # GET / — dashboard + daily modal
│   │   └── items.py       # Item CRUD endpoints that return HTMX fragments
│   ├── templates/
│   │   ├── base.html      # Shell: head, styles, HTMX include
│   │   ├── dashboard.html # Full-page layout
│   │   └── partials/      # HTMX fragments: row, modal, add form
│   └── static/
│       └── css/styles.css # All styling, incl. flash animation
├── tests/                 # pytest tests mirroring app/ structure
├── data/                  # SQLite file (gitignored)
├── requirements.txt
└── context/               # The six context files (this repo's docs)
```

- `models.py` owns **what data is stored**; it knows nothing about HTTP.
- `services.py` owns **what the data means** — turning raw rows into
  statuses/colors. This is the single source of truth for business rules.
- `routers/` owns **HTTP concerns only**: parse input, call crud/services,
  render a template fragment, return HTML.
- `templates/partials/` owns **reusable HTML fragments** HTMX swaps in.

## Storage Model

### Database (SQLite)

One table, `items`. Status is **derived, never stored** (see Invariants).

| Column | Type | Notes |
|---|---|---|
| `id` | integer PK | — |
| `name` | text | required |
| `category` | enum: `meds` / `food` / `household` | required, drives sort order |
| `quantity` | integer ≥ 0 | default 0 |
| `best_by_date` | date, nullable | **food only** — `null` for meds/household |
| `comment` | text, nullable | free-text note, inline-edited |
| `is_to_buy` | boolean | `true` = purple shopping-list item |
| `created_at` | datetime | audit/traceability |

Dates are stored as real dates (never strings) so that remote sync, if
added later, does not require a schema rewrite.

### Derived status (computed in `services.py`, not stored)

Priority order — the first match wins:

1. `is_to_buy` → **to-buy** (purple)
2. `quantity == 0` → **out-of-stock** (dark flashing red, never deleted)
3. `best_by_date` passed → **expired** (red; purged 7 days past best-by)
4. `best_by_date` ≤ 3 days away → **eat-soon** (yellow if 1–3, red if 0)
5. otherwise → **fine** (green)

### What does NOT live in the database

- **No file/blob storage** — no images, no receipts.
- **No cache** — single user, single machine; reads are cheap and local.
- **No auth tables** — there is no login (see below).

## Auth & Access Model

**None, by design.** Single user, single machine, local SQLite file. No
passwords, no accounts, no ownership checks. Every login screen is friction
that would defeat the ADHD-friendly goal.

Remote sync is explicitly **out of scope for v1**. Storing real dates keeps
the door open to adding it later without a schema rewrite — at which point
auth would become a first-class boundary, not a bolt-on.

## Real-Time Model

"Real-time" is achieved with HTMX, not WebSockets:

- **On load:** the server renders the full dashboard and the daily modal.
- **On action:** every button (`+`, `-`, set-to-0, `⟳`, save comment) is a
  `POST` that returns the updated HTML fragment, swapped in immediately.
- **On idle:** a polling trigger (`hx-trigger="every 10s"`) re-fetches the
  dashboard fragment so day rollovers and countdowns update without reload.

There are **no background jobs**. Expiry, countdowns, and the 7-day purge
are all computed lazily inside request handlers at read time.

## Invariants

1. **Status is always derived, never stored.** Expiry state, color, and
   sort position are computed from `quantity`, `best_by_date`, and
   `is_to_buy` at read time. The dashboard can never drift from real dates.
2. **`best_by_date` is food-only.** `meds` and `household` rows must have a
   `NULL` best-by date. Validation rejects any attempt to set one.
3. **Out-of-stock items are never auto-deleted.** Only date-expired items
   are purged, and only once 7 days past their best-by date.
4. **Sort order is fixed and enforced server-side:** out-of-stock → meds →
   food → household, each group sorted by urgency.
5. **No background jobs or schedulers.** All time-dependent behavior runs
   lazily in request handlers; the app stays single-process and stateless.
6. **Routers render fragments, not JSON.** HTMX endpoints return HTML
   partials. A JSON API is out of scope unless a consumer requires it.
7. **Business rules live only in `services.py`.** Routers and templates
   must not re-implement status/color/sort logic.