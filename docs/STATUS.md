# CCCb status

Snapshot of verified state. Re-measure and update this file when the code or the tests change.

Last verified: 2026-11-07, against `main` at `995e4f8` (before the documentation pass in this PR). Re-verify after this PR merges and record the merged commit here.

## Test results

| Setup | Result |
|---|---|
| With CNS 2.3.0 installed | 127 passed, 0 failed, 0 skipped |
| Without CNS | 34 passed, 1 skipped (the CNS connector test file, which skips when CNS is missing) |
| Lint (`ruff check .`) | Clean |

These counts come from the committed test suite. The repeated-passage sweep is not part of it (see below).

## Repeated-passage check

- Index design: each 40-character chunk is recorded at its first position only. The alignment step therefore tries one position per repeated chunk, not every position.
- Committed tests: `tests/test_repeated_passages.py` runs four deterministic scenarios (repeated in either text, reordered, overlapping, decoy continuations) and a seeded sweep of 120 cases. These run in CI.
- Manual sweep: `scripts/repeated_passage_sweep.py` runs 4,500 cases with repeated and decoy passages, compared against a brute-force longest-common-substring check. It is too slow for CI and is run by hand.
- Result (2026-11-07, main at `995e4f8`): 1 of 4,500 cases was reported shorter than the true overlap, by 1 character. The shared block appears twice in one text, and the matcher only aligned at the first occurrence. The duplicate flag was unaffected: any shared 40-character chunk already yields a span that clears the flag. The shortfall affects the reported length and score only.
- An earlier informal run reported 0 short cases. It used different random draws from the committed script, so it did not reproduce the case above. The committed script is the reference.
- Limit: these are sampled checks. They are evidence, not proof that the alignment is exhaustive. The known shortfall is a limitation of the current design, not a fixed behavior.

## CNS interaction: partial

- Implemented: the optional connector, tested with the real matcher over real texts.
- Not implemented: gates, verdict mapping, and chains. Nothing in this package builds them.
- Not integrated: no running flow calls the connector's binding check. CCC calls its own verdict-binding method instead.

## Known gaps

- The duplicate and recurrence thresholds live in CCCb, next to the math. CCC owns the decision about what a match means, but not yet these numbers.
- The duplicate score is a heuristic, not a calibrated probability. It does not account for searching across many prior records.
- Repeated chunks are aligned at their first position only. This can under-report the overlap length by a character or more (one case in the manual sweep). Whether to change the design is an open decision.
- Node.js 20 deprecation warnings appear in CI for the checkout and setup-python actions. Upgrade planned, not done.

## Known limits

- Indexes are in memory only, with no persistence.
- Comparison length is capped at 50,000 characters.
- The entropy figure is a fixed English estimate.
- Shared wording only, never shared meaning.

## Other repositories checked

Verified 2026-11-07: CCC (pin and injection), CNS (connector listing and the evidence spine), Link (pin and test import). Ecology's semantic provider was not checked.
