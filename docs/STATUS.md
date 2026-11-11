# CCCb status

Snapshot of verified state. Re-measure and update this file when the code or the tests change.

Last verified: 2026-11-10, on `main` at `5c1eff7` (merge of PR #15, which only changed docs after the code commit `737cf0e`). The GitHub Actions run for `5c1eff7` succeeded in all four jobs (Python 3.11 and 3.12, with and without CNS). The test counts below were re-run on `5c1eff7` the same day. Re-verify after the next merge and record the commit here.

## Test results

| Setup | Result |
|---|---|
| With CNS 3.0.0 installed | 129 passed, 0 failed, 0 skipped |
| Without CNS | 36 passed, 1 skipped (the CNS connector test file, which skips when CNS is missing) |
| Lint (`ruff check .`) | Clean |

These counts come from the committed test suite. The manual sweep is not part of it (see below).

## Repeated-passage alignment

- Each occurrence of a shared 40-character chunk is aligned, up to 32 occurrences per chunk per text (`MAX_OCCURRENCES_PER_SHINGLE`). The cap bounds the work on highly repetitive input.
- Before PR #14, each chunk was aligned at its first position only. That under-reported the overlap in one case of 4,500, by one character.
- Committed tests: `tests/test_repeated_passages.py` covers repeated passages in either text, reordering, overlap, decoy continuations, the failing case as a fixed regression test, and a timing check on repetitive input. A seeded sweep of 120 cases also runs in CI.
- Manual sweep: `scripts/repeated_passage_sweep.py` runs 4,500 cases against a brute-force longest-common-substring check. It takes about 14 seconds and is not in CI.
- Result (2026-11-10, `737cf0e`): 0 of 4,500 cases reported shorter than the true overlap.
- Limit: these are sampled checks, not a proof. The cap is an upper bound on alignments tried, so a very repetitive text can still be under-measured. The cap is deterministic.

## Behavior changed by PR #14

- Two existing tests had pinned the old under-report. The repeated-passage pair now measures 48 in both directions, which matches the true longest overlap. The old values were 48 and 45. The order still belongs to a finding, because the digest hashes the pair in order.

## CNS interaction: partial

- Implemented: the optional connector, tested with the real matcher over real texts.
- Not implemented: gates, verdict mapping, and chains. Nothing in this package builds them.
- Not integrated: no running flow calls the connector's binding check. CCC calls its own verdict-binding method instead.

## Known gaps

- The duplicate measure is easy to slip past: it is case and whitespace sensitive, needs a 40-character shared span, and reads only the first 50,000 characters. The recurrence measure flags the copies tried (upper-cased, doubled spaces, identical 38 characters, 80,000 characters of padding). CCC counts a recurrence as an occurrence, so a resubmission can advance a pattern. Whether to fix this in CCCb is an open decision. CCC's README records it as a known limit.
- The duplicate and recurrence thresholds live in CCCb, next to the math. CCC owns the decision about what a match means, but not yet these numbers.
- The duplicate score is a heuristic, not a calibrated probability. It does not account for searching across many prior records.
- Link pins CCCb to `8e3c779`, 20 commits behind `main` at `5c1eff7` and before the alignment fix. CCC pins `737cf0e`.
- Node.js 20 deprecation warnings appear in CI for the checkout and setup-python actions. Upgrade planned, not done.

## Known limits

- Indexes are in memory only, with no persistence.
- Comparison length is capped at 50,000 characters.
- Alignment tries at most 32 occurrences of each chunk per text.
- The entropy figure is a fixed English estimate.
- Shared wording only, never shared meaning.

## Other repositories checked

Verified 2026-11-10 by reading the current code and documents:

- CCC: pin (`737cf0e`), injection (runtime never imports CCCb; 11 test files do), and its description of the spine.
- CNS: `consumers.py` lists CCCb as an optional connector; the spine script `chains/evidence_spine.py` does not mention it.
- Link: pin and test import.
- observe-perceive: its CCC adapter imports `TextMatcher` from a sibling checkout.
- HERALD, Conservation_Kernel, Governance_Gateway: no reference to CCCb.
- TIE: no code reference. Its README describes CCCb as downstream in the spine, which does not match the CNS spine script.

- Ecology: `semantic_index.py` at the root of the Ecology repo defines `EcologySemanticIndex`, which implements the `SemanticIndex` interface that CCC defines in `ccc/semantic.py`. Read, not run.
