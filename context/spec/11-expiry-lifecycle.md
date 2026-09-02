# Unit 11: Expiry Lifecycle & Purge

## Goal

Implement the expiry lifecycle: food past its best-by becomes expired (red,
shown in the daily modal) and is purged exactly one week later. All computed
lazily at read time — no background jobs, no write-on-read.

## Design

Everything is derived from `best_by_date`. An item is expired when
`days_left < 0`; it is purged when `days_left <= -7`. Because the dashboard
is re-derived on every request, the transition happens automatically as
calendar days pass. No `expired_at` column is needed.

## Implementation

### services.py (defined in Unit 03)
- `is_expired(item, today)` → food and `days_left < 0`.
- `should_purge(item, today)` → food and `days_left <= -7`.

### Purge at read time
- The dashboard/list query excludes rows where `should_purge` is true
  (compute in Python, then delete them from the DB in the same request).
- The purge deletes only date-expired items; `quantity == 0` rows are never
  touched.

### Tests
`tests/test_expiry.py`:
- item at `days_left == -1` is expired and visible
- item at `days_left == -7` is purged; at `-6` it survives
- out-of-stock is never purged regardless of age
- meds/household are never expired or purged

## Dependencies

None new.

## Verify when done

- [ ] Expired food shows red and appears in the daily modal
- [ ] An item is purged exactly 7 days after its best-by date
- [ ] Out-of-stock items are never auto-deleted
