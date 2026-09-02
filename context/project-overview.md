# Household Inventory & Expiration Tracker

## Overview

A single-user web app that tracks household items — food, medications, and
household goods — along with how many are left and when food goes bad. It
solves the "things quietly rot in the back of the fridge" problem for someone
with ADHD: the app does the remembering by sorting everything into a
color-coded dashboard and showing a "what needs attention right now" modal
every time it opens. Built with FastAPI + HTMX + SQLite as a portfolio-grade
example of a practical, well-reasoned server-rendered SPA.

## Goals

1. Let the user add an item (name + quantity + category, and a best-by date
   for food) in a few seconds from a single modal.
2. Always surface what matters first: a dashboard sorted by urgency
   (out-of-stock → meds → food → household) with traffic-light colors.
3. Remind proactively: on every open, a modal shows "gone bad," "eat soon,"
   and "to-buy" items.
4. Keep the list trustworthy: date-expired items are purged after one week,
   while out-of-stock items never disappear so restocks aren't forgotten.
5. Stay zero-friction: no login, one device, plain CSS, no app to install.

## Core User Flow

1. **Open the app.** No login. The dashboard renders sorted by urgency, and
   the daily modal lists items that are gone bad, expiring soon, or on the
   to-buy list.
2. **Add an item.** Click "Add," pick a category (Meds / Food / Household),
   type a name and quantity, and — for food — a best-by date. The row appears
   in its sorted position with the correct color.
3. **Track usage.** Use the `+` / `-` buttons to change quantity, or "set to 0"
   when something is empty. A count of 0 turns the row dark flashing red and
   moves it to the very top, permanently.
4. **Restock.** Click `⟳` on any row to create a purple "to-buy" reminder.
   When the item is bought, click the purple row, enter the best-by date, and
   it becomes a normal green item.
5. **Plan ahead.** Add missing items directly as purple to-buys ("buy apples")
   without a date — they sit in the Food section until purchased.
6. **Annotate.** Click the empty comment cell on any row, type a note
   ("for Tuesday's recipe"), and save it inline.
7. **Let it run.** Food countdowns tick down automatically as real days pass.
   Expired items show in the daily modal for one week, then are deleted.

## Features

### Dashboard

- Traffic-light rows: green (fine), yellow (1–3 days left), red (0 or past),
  purple (to-buy), dark flashing red (out of stock).
- Fixed sort: out-of-stock first, then Meds, then Food, then Household;
  each group sorted by how soon food expires.
- "Real-time" via HTMX: buttons swap fragments immediately and the dashboard
  polls every 10 seconds, so day rollovers appear without a reload.

### Item Management

- Add-item modal: category, name, quantity, best-by date (food only).
- Per-row controls: `+`, `-`, set-to-0, and `⟳` (create a to-buy for the row).
- Inline-editable `comments` column, empty by default.

### Shopping List (To-Buy)

- Purple rows for items to buy; clicking a purchased row prompts for the
  best-by date and converts it to an active (green) item.

### Notification Modal

- Shown on every open, listing only: gone bad (past best-by), eat soon
  (1–3 days), and to-buy items. Out-of-stock and meds stay on the dashboard.

### Item Lifecycle

- Status is derived from data, never stored (see `architecture.md`).
- Active → expired (best-by passed) → deleted after 7 days.
- Out-of-stock (quantity 0) is permanent — never auto-deleted.

## Scope

### In Scope

- Single-user, single-machine local web app: FastAPI + HTMX + SQLite.
- Three categories with fixed sort order: Meds, Food, Household.
- Quantity tracking with `+` / `-` / set-to-0 / `⟳` controls.
- Best-by dates for food only; meds and household are count-only.
- Purple to-buy items and the buy-to-activate flow.
- Daily modal on every open (gone bad / eat soon / to-buy).
- Free-text comments column with inline editing.
- Plain CSS styling including the flashing out-of-stock animation.
- HTMX polling for live dashboard refresh.

### Out of Scope

- Authentication, accounts, or multi-user support.
- Remote sync / multi-device access (deferred — schema is sync-ready).
- Push, email, or phone notifications (in-app modal only).
- Barcode or receipt scanning.
- Storage locations (fridge / pantry / cabinet).
- Per-medication dosage schedules and reminders (future idea, needs its own
  design before it enters scope).
- Meal planning, recipes, or automatic shopping suggestions.
- A JSON REST API — HTMX endpoints return HTML fragments.
- Data import/export (revisit only if sync or backup is requested).

## Success Criteria

1. Opening the app shows the dashboard sorted out-of-stock → meds → food →
   household with correct colors, with no login and no page reloads.
2. Adding a food item with a best-by date places it in the correct sorted
   position with the correct color (green/yellow/red by days remaining).
3. Setting an item's quantity to 0 turns it dark flashing red, moves it to
   the top, survives a restart, and is never auto-deleted.
4. Clicking `⟳` creates a purple to-buy row; clicking that row prompts for a
   best-by date and converts it to a green active item.
5. The daily modal on open lists only gone-bad, eat-soon, and to-buy items.
6. A date-expired item is deleted exactly one week after it first expired.
7. Every action completes via HTMX fragment swap with no full page reload,
   and the dashboard self-refreshes within 10 seconds.
8. The pytest suite passes with no errors and no browser console errors.
