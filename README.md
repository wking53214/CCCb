# CCCb

Measures how alike two pieces of text are. It does not decide what that similarity means.

## What it measures

Both measurements are deterministic and need no outside dependencies.

| Measurement | Question it answers | Module |
|---|---|---|
| Duplicate | Is the overlap between two texts too long and specific to be coincidence? Short shared phrases are ignored; long, specific ones count. Produces an estimated coincidence score from the length of the matched text, using a fixed English information estimate (about 1.3 bits per character). | `cccb.matching` |
| Recurrence | Do two texts share enough meaningful vocabulary to look like the same pattern seen again? Compares sets of significant words (Jaccard overlap, threshold 0.5). Catches shared wording, not the same idea expressed differently. | `cccb.recurrence` |

`cccb.TextMatcher` bundles both behind three calls:

- `add(item_id, text)` returns nothing.
- `duplicate_of(text)` returns `(item_id, anti_probability, match_length)`, or `None` when nothing matches.
- `recurrence_of(text)` returns `(item_id, score, matches)`, or `None` when nothing matches.

`anti_probability` is the heuristic coincidence score described above. Indexes live in memory only, so a caller that persists texts must re-add them after a restart.

## Where it sits in the stack

CCCb is not a stage in the STACK spine. It is a library that serves one stage, CCC.

    HERALD --> TIE --> Conservation_Kernel --> Governance_Gateway --> CCC
                                                                       ^
                                                      CCCb plugs in here, from outside

- **The spine.** HERALD reads a document and extracts claims. TIE records them as evidence. Conservation_Kernel checks the transformation. Governance_Gateway checks admission. CCC judges whether the claim enters its store. CNS composes the chain and decides nothing. CCC's README owns this diagram.
- **Three jobs.** CCC decides what a match means. CCCb measures how alike two texts are. CNS binds a verdict to the content it judged.
- **Not a spine repo.** CNS's spine script does not mention CCCb, and none of HERALD, Conservation_Kernel or Governance_Gateway references it.

Who uses it (checked 2026-11-10):

| Repo | How it uses CCCb |
|---|---|
| CCC | Optional `match` extra, pinned to `737cf0e` (current main). Runtime code never imports CCCb; 11 test files do. |
| Link | Dev dependency pinned to older `8e3c779` (before the alignment fix). Used in one test. |
| observe-perceive | Its CCC adapter imports `TextMatcher` from a sibling checkout, not a pin. |
| CNS | Lists CCCb as an optional connector that loads `cns.gate` on demand. The spine script does not call it. |

## Using it with CCC

    from ccc import CCCSystem
    from cccb import TextMatcher

    system = CCCSystem(text_matcher=TextMatcher())

CCCb was split out of CCC at commit `d039efd`. Full history is in CCC's git log.

## What it does not do

- It stores no records and makes no decisions. Whether a duplicate counts as a new occurrence, or a recurrence may raise an anomaly, is CCC's rule.
- The duplicate measure is easy to slip past. It needs a 40-character shared span, treats upper and lower case and spacing as different, and reads only the first 50,000 characters. An upper-cased copy, a copy with doubled spaces, or an identical 38-character text is not called a duplicate. The recurrence measure does flag all of these (checked 2026-11-10), and CCC counts a recurrence as an occurrence, so a resubmission can advance a pattern. CCC lists this as a known limit.
- It does not prove a text is genuine. Two forgeries can match each other perfectly. A match only means the overlap is unlikely to be accidental.
- It is not semantic. Meaning-based similarity is handled separately: Ecology's `EcologySemanticIndex` implements CCC's `SemanticIndex` interface.
- It imports nothing from CCC or CNS when it loads. A test checks this with CNS blocked.

## Settings in force

| Setting | Value |
|---|---|
| Duplicate threshold | 1e-9 |
| Minimum match length | 40 characters |
| Recurrence threshold | 0.5 |
| Minimum signature size | 4 significant words |
| Maximum comparison length | 50,000 characters |

The duplicate score is a heuristic estimate, not a calibrated probability: the entropy figure is a fixed English estimate, and the score does not account for searching across many prior records.

## Optional CNS connector

CCCb runs without CNS. To use the connector, install with `pip install 'cccb[cns]'`. Without CNS, asking for a digest raises `CnsNotInstalled` and nothing else changes.

The connector (`cccb/cns_connector.py`) is the only place that knows CNS exists. It builds a finding for an ordered pair of texts: a hash of each text (the texts are not copied), the score, the thresholds in force, and whether the measurement cleared its threshold. A finding can be digested with CNS, and `binds` checks that a CNS gate result carries the same subject and digest as that finding. Change either text, swap the pair, or change a threshold, and the binding fails. Binding does not prove who issued the result, that it passed, or that anything was authorized.

The connector does not build gates, verdicts, or chains. It is a tested contract. No running flow in CCC or CNS calls `binds` from this package yet. (CCC calls its own verdict-binding method, which is a different function.)

Current status and test results are in [docs/STATUS.md](docs/STATUS.md).

## Tests

Run `pytest` from the repository root. Tests that need CNS skip when it is not installed. In CI, the CNS job installs the extra and fails instead of skipping. Lint runs with ruff.
