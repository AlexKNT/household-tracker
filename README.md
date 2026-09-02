# Household Inventory & Expiration Tracker

A single-user web app that tracks household items — food, medications, and
household goods — along with how many are left and when food goes bad. It
solves the "things quietly rot in the back of the fridge" problem for someone
with ADHD: the app does the remembering by sorting everything into a
color-coded dashboard and showing a "what needs attention right now" modal
every time it opens.

Built with **FastAPI + HTMX + SQLite** as a portfolio-grade example of a
practical, well-reasoned server-rendered SPA.

---

## Stack and why

| Layer | Technology | Why |
|---|---|---|
| Web framework | FastAPI | Async routing, Pydantic validation, thin routers |
| ASGI server | Uvicorn | Runs the FastAPI app with auto-reload for dev |
| ORM | SQLAlchemy 2.0 | Declarative models, typed queries, transactions |
| Database | SQLite | Single-file local storage — zero setup, zero ops |
| Templating | Jinja2 | Server-rendered HTML fragments for HTMX |
| Interactivity | HTMX | Partial page updates + polling, no JS framework |
| Styling | Plain CSS | Traffic-light status colors, one flash animation |
| Testing | pytest + httpx | Unit tests for domain logic, endpoint tests |

The full reasoning — including system boundaries, the storage model, the
derived-status rules, and the seven architecture invariants — lives in
[`context/architecture.md`](context/architecture.md). See
[`context/project-overview.md`](context/project-overview.md) for the product
vision, features, and scope.

The only third-party runtime dependencies are FastAPI, Uvicorn, SQLAlchemy,
Jinja2, and HTMX (a single vendored JS file). No background task framework,
no frontend build step, no login.

---

## Setup

1. **Create a virtual environment**

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**

   ```bash
   uvicorn app.main:app --reload
   ```

   Open <http://127.0.0.1:8000>. The SQLite database is created automatically
   on first run at `data/household.db` (gitignored).

---

## Testing

```bash
pytest
```

The suite covers the domain services (status derivation, sort order, expiry
math), the data model, every mutation endpoint over HTTP, and one test per
architecture invariant. It runs with no browser or external services.

---

## Feature tour

Follow the lifecycle of an item from the moment it enters the house to the
moment it leaves:

1. **Open the app.** No login. The dashboard renders sorted by urgency, and
   the daily modal lists items that are gone bad, expiring soon, or on the
   to-buy list.

2. **Add an item.** Click **Add item**, pick a category (Meds / Food /
   Household), type a name and quantity, and — for food — a best-by date. The
   row appears in its sorted position with the correct color.

3. **Track usage.** Use the `+` / `−` buttons to change quantity, or `0` to
   mark something empty. A count of 0 turns the row dark flashing red and
   moves it to the very top, permanently.

4. **Restock.** Click `⟳` on any row to create a purple "to-buy" reminder.
   When the item is bought, click the purple row, enter the best-by date, and
   it becomes a normal green item.

5. **Plan ahead.** Add missing items directly as purple to-buys ("buy
   apples") without a date — they sit in their section until purchased.

6. **Annotate.** Click the empty comment cell on any row, type a note ("for
   Tuesday's recipe"), and save it inline.

7. **Let it run.** Food countdowns tick down automatically as real days pass.
   Expired items show in the daily modal for one week, then are deleted.
   Out-of-stock items are never auto-deleted, so a restock is never forgotten.

Every action is an HTMX fragment swap — no full page reloads — and the
dashboard self-refreshes every 10 seconds.

---

## Project layout

```
app/
├── main.py            # App factory, route registration, static mount
├── config.py          # Settings (DB path, thresholds, polling interval)
├── db.py              # Engine, session factory, Base
├── models.py          # SQLAlchemy ORM models (Category + Item)
├── schemas.py         # Pydantic schemas for forms
├── crud.py            # Data access: queries and mutations
├── services.py        # Domain logic: status/color/sort/expiry
├── routers/           # dashboard.py + items.py (return HTMX fragments)
├── templates/         # base.html, dashboard.html, partials/
└── static/            # css/styles.css, js/htmx.min.js
tests/                 # pytest suite mirroring app/
data/                  # SQLite file (gitignored)
context/               # The six context files + per-unit specs
docs/                  # schema.md
```
