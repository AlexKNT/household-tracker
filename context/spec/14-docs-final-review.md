# Unit 14: Docs & Final Review

## Goal

Finish the portfolio: a project `README.md` (what it does, stack, run/test/
demo), a final invariants audit, and syncing every context file to the
implemented state.

## Design

This unit produces no application code — it verifies and documents. The
`README.md` must let a stranger run, test, and demo the app from a cold
clone.

## Implementation

### README.md (project root)
- One-line description + ADHD context.
- Stack and why (point to `context/architecture.md`).
- Setup: create venv, `pip install -r requirements.txt`, run uvicorn.
- Testing: `pytest`.
- Feature tour with the item lifecycle.

### Invariants audit
Walk `architecture.md` invariants 1–7 and confirm each holds in code, citing
the file/function that enforces it.

### Context sync
Verify `project-overview.md` success criteria are all demonstrably true, and
update `architecture.md`, `code-standards.md`, `ui-context.md`, and
`progress-tracker.md` where implementation diverged from the docs.

## Dependencies

None new.

## Verify when done

- [ ] `README.md` lets a stranger run, test, and demo the app
- [ ] All success criteria in `project-overview.md` are demonstrably true
- [ ] Context files accurately reflect the finished implementation
