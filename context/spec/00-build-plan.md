# Build Plan — Smart Household Inventory & Expiration Tracker

Spec-driven build in 15 units. Each unit has a spec file in this folder
(`NN-name.md`), produced just-in-time before implementation. Units are
ordered so every unit builds only on things that already exist.

## How to Use This Plan

1. Work one unit at a time, in order.
2. Read the unit's spec file, mark it in progress in
   `context/progress-tracker.md`, implement, verify, mark complete.
3. Never start unit N until every unit before it is verified.
4. If a unit changes the architecture, scope, or standards, update the
   relevant `context/*.md` file before continuing.

## Spec File Naming Convention

`NN-name.md`, zero-padded, matching the unit number below. The number is the
build order; the name is the unit's focus.

## Unit Overview

| # | Spec file | Builds | Depends on |
|---|---|---|---|
| 00 | `00-project-scaffold.md` | Runnable FastAPI skeleton, config, templates, CSS shell, pytest harness | — |
| 01 | `01-db-plan.md` | Detailed database spec: DDL, constraints, indexes, migration approach | 00 |
| 02 | `02-db-implementation.md` | `db.py`, `models.py`, enums, migration, model tests | 01 |
| 03 | `03-domain-services.md` | Status derivation, sort order, expiry math in `services.py` + tests | 02 |
| 04 | `04-dashboard.md` | Grouped, sorted, color-coded dashboard with HTMX polling | 03 |
| 05 | `05-notification-modal.md` | Daily modal (gone bad / eat soon / to-buy) on every load | 04 |
| 06 | `06-add-item.md` | Add-item modal + `POST /items` with validation and fragments | 03, 04 |
| 07 | `07-to-buy.md` | Purple to-buy items + buy-to-activate flow | 06 |
| 08 | `08-quantity-controls.md` | `+`, `-`, set-to-0 endpoints; out-of-stock behavior | 03, 06 |
| 09 | `09-restock.md` | `⟳` button creates a to-buy from any row | 08 |
| 10 | `10-comments.md` | Inline-editable comments column + `PATCH` endpoint | 06 |
| 11 | `11-expiry-lifecycle.md` | Expired state, 7-day purge, lifecycle tests | 03, 08 |
| 12 | `12-ui-polish.md` | Full token styling, responsive, empty states, flash animation | 04 |
| 13 | `13-testing-hardening.md` | Full pytest suite, edge cases, end-to-end pass | 11, 12 |
| 14 | `14-docs-final-review.md` | Invariants audit, docs sync, portfolio README, run instructions | 13 |

---

## Phase 0 — Foundation

### Unit 00 — Project Scaffold

**Builds:** the runnable application skeleton. A FastAPI app factory in
`app/main.py`, `config.py` (DB path, thresholds, polling interval), static
mount, a `base.html` template shell that includes HTMX and `styles.css`, an
empty dashboard route returning a placeholder page, and a pytest + httpx
test harness with one smoke test.

**Depends on:** nothing.

**Done when:**
- `uvicorn app.main:app` serves the dashboard route with no errors.
- HTMX and the stylesheet load in the browser.
- `pytest` runs and passes the smoke test.

### Unit 01 — DB Plan

**Builds:** a written database spec (a new `context/spec/01-db-plan.md`, or a
dedicated `docs/schema.md`) that translates `architecture.md` into exact DDL —
the `items` table with every column, type, nullability, default, constraint,
and index. Includes the `category` enum values and the derived-status rules as
comments. Decides and documents the migration strategy (Alembic vs.
`create_all` for v1) and the `data/` file location.

**Depends on:** 00 (needs the project layout to reference paths).

**Done when:**
- The spec pins every column/type/constraint with no ambiguity.
- Nullability matches `architecture.md` (e.g. `best_by_date` nullable, food-only).
- Migration strategy is chosen and documented.

### Unit 02 — DB Implementation

**Builds:** the working data layer. `app/db.py` (engine, session factory,
`Base`), `app/models.py` (SQLAlchemy 2.0 `Mapped[...]` model for `items` with
the `Category` enum column), the chosen migration mechanism, and a
`tests/test_models.py` proving the table can be created and a row round-trips.

**Depends on:** 01.

**Done when:**
- The schema is created exactly as planned in 01.
- An item row can be inserted, fetched, and updated via a session.
- Model tests pass.

---

## Phase 1 — Domain Core

### Unit 03 — Domain Services

**Builds:** `app/services.py` — the single source of truth for business rules:
status derivation (to-buy → out-of-stock → expired → eat-soon → fine), the
traffic-light mapping from days-left, the fixed sort order
(out-of-stock → meds → food → household), and the expiry/7-day-purge math.
Exhaustive unit tests cover every status branch and the invariants.

**Depends on:** 02.

**Done when:**
- Every status transition and color rule is unit-tested, including edge days
  (0, 1, 3, 4).
- Sort order is enforced in code and tested.
- No status/color/sort logic lives outside `services.py`.

---

## Phase 2 — Read Path

### Unit 04 — Dashboard

**Builds:** the dashboard page. `routers/dashboard.py` (`GET /`) queries items,
derives statuses via `services.py`, groups and sorts them, and renders
`dashboard.html` with category sections and color-coded rows. Includes the
HTMX polling trigger (`hx-trigger="every 10s"`) and a friendly empty state.
Uses seed/placeholder data; no mutations yet.

**Depends on:** 03.

**Done when:**
- The page renders out-of-stock → meds → food → household with correct colors.
- A food item shows "N days left" and its best-by date.
- The dashboard auto-refreshes within 10 seconds.

### Unit 05 — Notification Modal

**Builds:** the daily modal shown on every page load, listing only three
groups in order: Gone bad, Eat soon, To-buy. Dismissible, no persistence
required (shows every load by design). Rendered server-side in the dashboard
response.

**Depends on:** 04.

**Done when:**
- Opening the app shows the modal with the three correct groups.
- Out-of-stock and meds do NOT appear in the modal.
- The modal is dismissible and reappears on the next full load.

---

## Phase 3 — Write Path

### Unit 06 — Add Item

**Builds:** the add-item modal and `POST /items`. A form with category, name,
quantity, and best-by date (rendered/required only for food). Pydantic
validation in `schemas.py` rejects best-by dates on meds/household. Returns an
HTMX fragment that inserts the new row in its correct sorted position.

**Depends on:** 03 (status/sort), 04 (dashboard fragment swap).

**Done when:**
- Adding a food item places it correctly sorted and colored with no reload.
- Adding a med/household item with a date is rejected.
- Empty/invalid input shows a validation error, not a crash.

### Unit 07 — To-Buy

**Builds:** purple shopping-list items. Adding a missing item as a to-buy
(date defaults to today, `is_to_buy=true`, purple). The buy-to-activate flow:
clicking a purple row opens a small modal to enter the best-by date, which
flips the row to an active (green) item.

**Depends on:** 06.

**Done when:**
- A to-buy item renders purple and sorts within its category.
- Clicking a purple row prompts for best-by and converts it to green.
- To-buy items appear in the daily modal's "To-buy" group.

### Unit 08 — Quantity Controls

**Builds:** the `+`, `-`, and set-to-0 row controls as HTMX POST endpoints
returning the updated row fragment. Quantity is clamped at 0. Reaching 0
turns the row out-of-stock: dark flashing red, moved to the very top,
never deleted.

**Depends on:** 03 (out-of-stock status), 06 (rows exist).

**Done when:**
- `+` / `-` update the quantity and re-render the row in place.
- Setting to 0 makes the row dark flashing red and moves it to the top.
- An out-of-stock row persists across reloads.

### Unit 09 — Restock (⟳)

**Builds:** the `⟳` button on each row, which creates a purple to-buy item for
that row's name/category. Used to restock an out-of-stock item or re-order
anything. Returns a fragment updating the dashboard.

**Depends on:** 08 (button lives on the row), 07 (to-buy model).

**Done when:**
- Clicking `⟳` creates a to-buy for the row's item.
- The new to-buy appears in its category in purple and in the modal.

### Unit 10 — Comments

**Builds:** the inline-editable comments column. Empty by default; clicking a
cell turns it into an input; saving via `PATCH /items/{id}/comment` persists
the text and re-renders the cell. Uses HTMX's inline-edit pattern, no JS.

**Depends on:** 06 (items and rows exist).

**Done when:**
- Clicking an empty comment cell lets the user type and save.
- The saved comment persists across reloads.
- Editing uses only HTMX attributes.

---

## Phase 4 — Lifecycle & Cleanup

### Unit 11 — Expiry Lifecycle & Purge

**Builds:** the expiry lifecycle. When food passes its best-by, it becomes
"expired" (red) and is included in the daily modal. Exactly 7 days after the
best-by date, it is deleted. All derived lazily at read time — no background
jobs, no stored expiry timestamp. Tests cover the full timeline, including
the out-of-stock never-deleted invariant.

**Depends on:** 03 (expiry math), 08 (statuses coexist).

**Done when:**
- Expired food shows red and appears in the modal.
- An item is deleted exactly 7 days after its best-by date.
- Out-of-stock items are never auto-deleted.

---

## Phase 5 — Polish & Portfolio

### Unit 12 — UI Polish & Responsive

**Builds:** the final visual layer using only `ui-context.md` tokens: the full
`styles.css` with status triples, sticky header, category sections, modals,
focus states, and the single `flash` animation. Mobile-first responsive layout
and friendly empty states for every section.

**Depends on:** 04 (the dashboard exists to style).

**Done when:**
- No hardcoded hex values outside `:root`.
- Only the out-of-stock flash animation exists.
- Layout is usable at mobile and desktop widths.

### Unit 13 — Testing & Hardening

**Builds:** the complete pytest suite — unit tests for services and models,
endpoint tests via httpx `TestClient` for every mutation, and explicit tests
for each invariant in `architecture.md`. Edge cases: day boundaries, quantity
clamping, category/date mismatch, comment editing, purge timing.

**Depends on:** 11, 12.

**Done when:**
- `pytest` passes with no failures.
- Every invariant has at least one test asserting it.
- No browser console errors on a manual pass.

### Unit 14 — Docs & Final Review

**Builds:** the portfolio finish. A project `README.md` (what it does, stack,
how to run, test, and demo), a final invariants audit against
`architecture.md`, and syncing every `context/*.md` file to the implemented
state. Verifies the whole app end to end against `project-overview.md`
success criteria.

**Depends on:** 13.

**Done when:**
- `README.md` lets a stranger run, test, and demo the app.
- All success criteria in `project-overview.md` are demonstrably true.
- Context files accurately reflect the finished implementation.

---

## Dependency Graph (text)

```
00 → 01 → 02 → 03 → 04 → 05
                    ↘ 06 → 07
                    ↘ 08 → 09
                    ↘ 06 → 10
03,08 → 11
04 → 12
11,12 → 13 → 14
```

## Out of Scope (deferred — do not build in this plan)

- Auth, accounts, multi-user, remote sync
- Push/email notifications (in-app modal only)
- Barcode/receipt scanning, storage locations
- Per-medication dosage schedules
- JSON API, data import/export
