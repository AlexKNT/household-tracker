# UI Context

## Theme

Light only — calm, warm, and high-contrast. The design language is a clean
"kitchen inventory" feel: warm off-white background, white rows, and vivid
semantic status colors that do the heavy lifting so the eye finds urgency
instantly. No dark mode. No gradients. No shadows beyond a subtle lift on
the modal and sticky header. The status color of a row is the single source
of truth for urgency — never decorate with additional colors.

## Colors

Define all colors as CSS custom properties on `:root`. Components must use
these tokens — no hardcoded hex values anywhere else in the CSS.

```css
:root {
  /* Neutrals */
  --bg:            #F7F6F3;  /* page background */
  --surface:       #FFFFFF;  /* rows, cards, modal */
  --surface-alt:   #EFEDE8;  /* section headers, hover */
  --border:        #E2DFD9;  /* hairline separators */
  --text:          #1A1815;  /* primary text */
  --text-muted:    #6B675F;  /* dates, counts, meta */

  /* Semantic status — background / border / text triples */
  --green-bg:      #E8F5E9;  --green-border: #2E7D32;  --green-text: #1B5E20;
  --yellow-bg:     #FFF8E1;  --yellow-border:#F9A825;  --yellow-text:#7A5B00;
  --red-bg:        #FDECEA;  --red-border:   #C62828;  --red-text:   #7F1D1D;
  --purple-bg:     #F3E5F5;  --purple-border:#7B1FA2;  --purple-text:#4A148C;

  /* Out-of-stock: solid dark flashing red (white text) */
  --out-bg:        #8C1D1D;
  --out-text:      #FFFFFF;

  /* Actions */
  --accent:        #1B6EF3;  /* primary button (Add) */
  --accent-hover:  #155ACB;
  --danger:        #C62828;  /* destructive hover */
  --focus-ring:    #1B6EF3;
}
```

Usage rules:

- A row's **background, left border, and text** all come from the same status
  triple (e.g. yellow row = `--yellow-bg` background, `--yellow-border` left
  accent, `--yellow-text` name).
- **Out-of-stock** rows ignore the triple and use `--out-bg` background with
  `--out-text` text, animated with the `flash` keyframes below.
- Neutral surfaces (`--surface`, `--border`, `--text`, `--text-muted`) are the
  only colors allowed outside status styling.

## Typography

System font stack — no webfonts, no build step:

```css
font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
```

| role | size / weight | notes |
|---|---|---|
| page title | 1.5rem / 700 | dashboard heading |
| item name | 1rem / 600 | row primary text |
| meta (date, count, days-left) | 0.875rem / 400 | `--text-muted` |
| section header | 0.75rem / 700, uppercase, +0.08em letter-spacing | "Meds", "Food", "Household" |
| button glyphs (+, −, 0, ⟳) | 1rem / 700 | monospace feel, large tap target |

## Border Radius

| token | value | use |
|---|---|---|
| `--radius-sm` | 6px | buttons, chips |
| `--radius-md` | 10px | rows, inputs |
| `--radius-lg` | 16px | modal, cards |

## Layout Patterns

- **Single column, centered.** The dashboard is one column, `max-width: 900px`,
  centered with generous padding. No sidebar. One screen, one job.
- **Sticky header** with the app title and a single primary **"Add item"**
  button (right-aligned). The header stays visible while scrolling.
- **Category sections.** Items are grouped under uppercase section headers in
  this fixed order: **Out of stock → Meds → Food → Household**. Each section
  is a stack of rows sorted by urgency.
- **Row anatomy** (left → right):
  1. Button cluster: `+` and `-` stacked, `0` below, `⟳` to the right of `0`.
  2. Item name (status-colored text).
  3. Meta: quantity badge and, for food, "N days left" + the best-by date.
  4. Comment cell (right-aligned, muted; empty by default, click to edit).
- **Modal.** Centered overlay (`position: fixed`) over a dimmed backdrop;
  card uses `--radius-lg` and `--surface`. Used for: add item, buy-to-activate
  (enter best-by), and the daily notification modal.
- **Daily notification modal.** Shown on every page load, dismissible. Lists
  three groups in order: Gone bad, Eat soon, To-buy. Items here are plain text
  lines, not interactive rows.
- **Focus states.** Every button and input gets a visible `--focus-ring`
  outline for keyboard accessibility.

## Icons

No icon library. The row controls use plain text glyphs — `+`, `−`, `0`, `⟳`
— styled with CSS, so there are no image assets or icon dependencies. Any
additional UI icon is an inline SVG, kept minimal and current-color-aware.

## Animation

Only one animation exists: the out-of-stock flash.

```css
@keyframes flash {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.55; }
}

.row--out { animation: flash 1.4s ease-in-out infinite; }
```

No other elements animate. Motion is reserved for the single most urgent
signal, so it never competes for attention.