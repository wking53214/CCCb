# CCCb status

Snapshot of verified state. Re-measure and update this file when the code or the tests change.

Last verified: 2026-11-07, at commit `f338063`.

## Test results

| Setup | Result |
|---|---|
| With CNS 2.3.0 installed | 122 passed, 0 failed, 0 skipped |
| Without CNS | 29 passed, 1 skipped (the CNS connector test file, which skips when CNS is missing) |
| Lint (`ruff check .`) | Clean |

## CNS interaction: partial

- Implemented: the optional connector, tested with the real matcher over real texts.
- Not implemented: gates, verdict mapping, and chains. Nothing in this package builds them.
- Not integrated: no running flow calls the connector's binding check. CCC calls its own verdict-binding method instead.

## Known gaps

- The duplicate and recurrence thresholds live in CCCb, next to the math. CCC owns the decision about what a match means, but not yet these numbers.

## Known limits

- Indexes are in memory only, with no persistence.
- Comparison length is capped at 50,000 characters.
- The entropy figure is a fixed English estimate.
- Shared wording only, never shared meaning.

## Other repositories checked

Verified 2026-11-07: CCC (pin and injection), CNS (connector listing and the evidence spine), Link (pin and test import). Ecology's semantic provider was not checked.
