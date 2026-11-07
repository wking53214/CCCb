# CCCb

Measures how alike two pieces of text are. It does not decide what that similarity means.

## What it measures

Both measurements are deterministic and need no outside dependencies.

| Measurement | Question it answers | Module |
|---|---|---|
| Duplicate | Is the overlap between two texts too long and specific to be coincidence? Short shared phrases are ignored; long, specific ones count. Produces an estimated coincidence score from the length of the matched text, using a fixed English information estimate (about 1.3 bits per character). | `cccb.matching` |
| Recurrence | Do two texts share enough meaningful vocabulary to look like the same pattern seen again? Compares sets of significant words (Jaccard overlap, threshold 0.5). Catches shared wording, not the same idea expressed differently. | `cccb.recurrence` |

`cccb.TextMatcher` bundles both behind three calls: `add`, `duplicate_of`, and `recurrence_of`. They return plain strings and numbers. Indexes live in memory only, so a caller that persists texts must re-add them after a restart.

## Using it with CCC

    from ccc import CCCSystem
    from cccb import TextMatcher

    system = CCCSystem(text_matcher=TextMatcher())

## What it does not do

- It stores no records and makes no decisions. Whether a duplicate counts as a new occurrence, or a recurrence may raise an anomaly, is CCC's rule.
- It does not prove a text is genuine. Two forgeries can match each other perfectly. A match only means the overlap is unlikely to be accidental.
- It is not semantic. Meaning-based similarity is handled separately (Ecology's `SemanticIndex`, plugged into CCC).
- It imports nothing from CCC or CNS when it loads. A test checks this with CNS blocked.

## Settings in force

| Setting | Value |
|---|---|
| Duplicate threshold | 1e-9 |
| Minimum match length | 40 characters |
| Recurrence threshold | 0.5 |
| Minimum signature size | 4 significant words |
| Maximum comparison length | 50,000 characters |

The duplicate score is a heuristic estimate, not a calibrated probability: the entropy figure is a fixed English estimate, and the score does not account for searching across many prior records. Comparisons measure shared wording only, never shared meaning.

## Optional CNS connector

CCCb runs without CNS. To use the connector, install with `pip install 'cccb[cns]'`. Without CNS, asking for a digest raises `CnsNotInstalled` and nothing else changes.

The connector (`cccb/cns_connector.py`) is the only place that knows CNS exists. It builds a finding for an ordered pair of texts: a hash of each text (the texts are not copied), the score, the thresholds in force, and whether the measurement cleared its threshold. A finding can be digested with CNS, and `binds` checks that a CNS gate result carries the same subject and digest as that finding. Change either text, swap the pair, or change a threshold, and the binding fails. Binding does not prove who issued the result, that it passed, or that anything was authorized.

The connector does not build gates, verdicts, or chains. It is a tested contract. No running flow in CCC or CNS calls `binds` from this package yet. (CCC calls its own verdict-binding method, which is a different function.)

## Where it fits

- CCC receives the matcher by injection. Its runtime code never imports CCCb, though its test suite does.
- CCC and Link pin CCCb to commit `8e3c779`. Link uses it in a test.
- CNS lists CCCb as an optional connector that loads CNS only on demand.
- CCCb was split out of CCC at commit `d039efd`. Full history is in CCC's git log.

Current status and test results are in [docs/STATUS.md](docs/STATUS.md).

## Tests

Run `pytest` from the repository root. Tests that need CNS skip when it is not installed. In CI, the CNS job installs the extra and fails instead of skipping. Lint runs with ruff.
