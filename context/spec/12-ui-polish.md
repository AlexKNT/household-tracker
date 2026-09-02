# Unit 12: UI Polish & Responsive

## Goal

Implement the full visual layer from `ui-context.md`: all CSS custom
properties, the status triples, sticky header, category sections, modals,
focus states, the single flash animation, and a mobile-first responsive
layout.

## Design

Tokens live in `:root` in `styles.css`; no hex values appear anywhere else.
The only animation is `@keyframes flash` on `.row--out`. The layout is a
single centered column (max-width 900px), mobile-first.

## Implementation

### app/static/css/styles.css
- `:root` tokens exactly as defined in `ui-context.md`.
- Reset + base typography (system font stack).
- Status classes `row--green/yellow/red/purple/out` applying the
  background/border/text triples; `.row--out` uses `--out-bg`/`--out-text`
  plus the `flash` animation.
- Sticky header, section headers, row grid, button styles.
- Modal overlay + card styles; focus-visible rings.
- Responsive breakpoints (stack controls and meta on narrow screens).
- Empty-state styles.

### Template cleanup
Apply the classes consistently across `dashboard.html`, `row.html`, modal
fragments, and forms.

## Dependencies

None new.

## Verify when done

- [ ] No hardcoded hex values outside `:root`
- [ ] Only the out-of-stock flash animation exists
- [ ] Layout is usable at mobile and desktop widths
- [ ] Focus states are visible on all buttons and inputs
