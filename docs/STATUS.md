# CCCb status

Snapshot of verified state. Re-measure and update this file when the code or the tests change.

Last verified: 2026-11-07, on branch `fix/align-repeated-chunks` (based on `docs/audit-pass`, which is `main` at `995e4f8` plus the documentation pass). Record the merged commit here after merge and re-verify.

## Test results

| Setup | Result |
|---|---|
| With CNS 2.3.0 installed | 129 passed, 0 failed, 0 skipped |
| Without CNS | 36 passed, 1 skipped (the CNS connector test file, which skips when CNS is missing) |
| Lint (`ruff check .`) | Clean |

These counts come from the committed test suite. The manual sweep is not part of it (see below).

## Repeated-passage alignment

- Each occurrence of a shared 40-character chunk is aligned, up to 32 occurrences per chunk per text (`MAX_OCCURRENCES_PER_SHINGLE`). The cap bounds the work on highly repetitive input.
- Before this change, each chunk was aligned at its first position only. That under-reported the overlap in one case of 4,500, by one character. The fix is in this branch.
- Committed tests: `tests/test_repeated_passages.py` covers repeated passages in either text, reordering, overlap, decoy continuations, the failing case as a fixed regression test, and a timing check on repetitive input. A seeded sweep of 120 cases also runs in CI.
- Manual sweep: `scripts/repeated_passage_sweep.py` runs 4,500 cases against a brute-force longest-common-substring check. It takes about 14 seconds and is not in CI.
- Result after the fix: 0 of 4,500 cases reported shorter than the true overlap.
- Limit: these are sampled checks, not a proof. The cap is an upper bound on alignments tried, so a very repetitive text can still be under-measured. The cap is deterministic.

## Behavior changed by this fix

- Two existing tests had pinned the old under-report. The repeated-passage pair now measures 48 in both directions, which matches the true longest overlap. The old values were 48 and 45. The order still belongs to a finding, because the digest hashes the pair in order.

## CNS interaction: partial

- Implemented: the optional connector, tested with the real matcher over real texts.
- Not implemented: gates, verdict mapping, and chains. Nothing in this package builds them.
- Not integrated: no running flow calls the connector's binding check. CCC calls its own verdict-binding method instead.

## Known gaps

- The duplicate and recurrence thresholds live in CCCb, next to the math. CCC owns the decision about what a match means, but not yet these numbers.
- The duplicate score is a heuristic, not a calibrated probability. It does not account for searching across many prior records.
- Node.js 20 deprecation warnings appear in CI for the checkout and setup-python actions. Upgrade planned, not done.

## Known limits

- Indexes are in memory only, with no persistence.
- Comparison length is capped at 50,000 characters.
- Alignment tries at most 32 occurrences of each chunk per text.
- The entropy figure is a fixed English estimate.
- Shared wording only, never shared meaning.

## Other repositories checked

Verified 2026-11-07: CCC (pin and injection), CNS (connector listing and the evidence spine), Link (pin and test import). Ecology's semantic provider was not checked.
