# Unit 13: Testing & Hardening

## Goal

Complete the test suite: unit tests for services and models, endpoint tests
for every mutation via httpx, and explicit tests for each architecture
invariant. Edge cases included.

## Design

Tests mirror the `app/` structure. Services are pure functions (fast unit
tests); endpoints use `TestClient` against a temp SQLite database. Each
invariant in `architecture.md` maps to at least one test.

## Implementation

### Coverage targets
- `tests/test_services.py` — every status branch and day boundary (−7, −1,
  0, 1, 3, 4), color mapping, sort order, purge window.
- `tests/test_models.py` — schema nullability and round-trip.
- `tests/test_endpoints.py` — add, activate, increment/decrement/empty,
  restock, comment, dismiss modal.
- `tests/test_invariants.py` — one test per architecture invariant.

### Edge cases to cover
- quantity clamping at 0; `-` at 0 is a no-op
- best-by on meds/household rejected
- to-buy with/without date; activating sets best-by
- comment save and empty comment
- purge exactly at the −7 boundary

## Dependencies

None new (`pytest`, `httpx` already present).

## Verify when done

- [ ] `pytest` passes with no failures
- [ ] Every invariant has at least one asserting test
- [ ] No browser console errors on a manual pass
