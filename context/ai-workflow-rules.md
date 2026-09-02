# AI Workflow Rules

## Approach

Build this project incrementally using a spec-driven workflow. The six
context files define what to build, how to build it, and the current state
of progress; `context/spec/00-build-plan.md` defines the ordered units. Each
unit is implemented from its spec, verified against its checklist, then
marked complete in `progress-tracker.md`. Always implement against these
specs — do not infer or invent behavior from scratch.

## Scoping Rules

- Work on one feature unit at a time.
- Prefer small, verifiable increments over large speculative changes.
- Do not combine unrelated system boundaries in a single step (e.g. DB
  schema + business rules + HTML changes at once).
- Introduce dependencies just in time: install a package only in the unit
  where it first unlocks real behavior.
- Build backend before frontend wiring; build UI shells before real data.

## When to Split Work

Split an implementation step if it combines:

- DB/model changes with router or template changes
- Multiple unrelated endpoints or fragments
- Behavior not clearly defined in the context files or unit spec
- A new dependency together with the feature that uses it

If a change cannot be verified end to end quickly (run pytest, open the
page, click through), the scope is too broad — split it.

## Handling Missing Requirements

- Do not invent product behavior not defined in the context files or the
  unit spec.
- If a requirement is ambiguous, resolve it in the relevant context file —
  or ask — before implementing.
- If a requirement is missing, add it as an open question in
  `progress-tracker.md` before continuing.
- Never silently change a locked decision (sort order, status priority,
  colors, thresholds). Record the change in the context file first.

## Protected Files

Do not modify the following unless explicitly instructed:

- The six `context/*.md` files beyond what the current task authorizes;
  `progress-tracker.md` is updated as part of the normal workflow.
- `spec/00-build-plan.md` — units are added or removed deliberately, not
  rewritten mid-build.
- `requirements.txt` — change only when a new dependency is approved.
- The virtual environment (`.venv/`) and any third-party library internals.

## Keeping Docs in Sync

Update the relevant context file whenever implementation changes:

- System architecture or boundaries → `architecture.md`
- Storage model decisions → `architecture.md`
- Code conventions or standards → `code-standards.md`
- Feature scope → `project-overview.md`
- Visual or animation decisions → `ui-context.md`

`progress-tracker.md` is updated after every meaningful implementation change.

## Before Moving to the Next Unit

1. The current unit works end to end within its defined scope.
2. No invariant defined in `architecture.md` was violated.
3. `pytest` passes with no failures and there are no browser console errors.
4. The behavior satisfies every item in the unit's verification checklist.
5. `progress-tracker.md` reflects the completed work.