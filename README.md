# CCCb

Measures how alike two pieces of text are. Nothing else.

## What it does

Two measurements, both deterministic, explainable and dependency-free:

| measurement | question it answers | module |
|---|---|---|
| duplicate | Is the overlap between two texts too long and specific to be coincidence? Uses the information content of the matched text (Shannon's ~1.3 bits per character of English), so a short shared phrase is unremarkable and a long, specific one is not. | `cccb.matching` |
| recurrence | Do two texts share enough significant vocabulary to be the same pattern seen again, even with different evidence? Concept-set overlap (Jaccard, threshold 0.5). Catches shared wording, not the same idea in different words. | `cccb.recurrence` |

`cccb.TextMatcher` bundles both behind the interface CCC plugs in: `add`,
`duplicate_of`, `recurrence_of`, all returning plain strings and numbers.

## What it does not do

- It holds no records and makes no decisions. Whether a duplicate counts as a
  new occurrence, or whether a recurrence may raise an anomaly to a pattern, is
  CCC's rule, not this package's.
- It does not prove anything is genuine. Two forgeries can match each other
  perfectly; a match only says the overlap is not plausibly accidental.
- It is not semantic. Meaning-based similarity plugs into CCC separately
  (Ecology's `SemanticIndex` provider).
- It imports nothing from CCC, and a test enforces that.

## Where it came from

Split out of [CCC](https://github.com/wking53214/CCC) at commit `d039efd`, when
CCC was narrowed to one job (remembering claims over time so a machine cannot
rewrite what a human thought). `matching.py`, `recurrence.py`, the
known-boilerplate list and their direct tests moved here unchanged apart from
import paths and a provenance note. Full history is in CCC's git log.

## Using it with CCC

    from ccc import CCCSystem
    from cccb import TextMatcher

    system = CCCSystem(text_matcher=TextMatcher())

## Optional CNS connection

CCCb does not need CNS. It has no runtime dependency, nothing in the package imports CNS when it loads (and nothing imports CCC), and `tests/test_cns_independence.py` checks this with CNS blocked. `cccb/cns_connector.py` is the one place that knows CNS exists. Install it with `pip install 'cccb[cns]'`; without CNS, asking for a digest raises `CnsNotInstalled` and nothing else changes.

**What is bound.** One measurement of an ordered pair of texts (the new text, then the earlier one it was compared with), as a `DuplicateFinding` (`duplicate_finding(a, b)`) or a `RecurrenceFinding` (`recurrence_finding(a, b)`): the SHA-256 of each text (the texts are not copied), the measurement kind, the score, the threshold and minimum in force, and the result. `duplicate_digest` / `recurrence_digest` hash that with `cns.gate.subject_digest`, and `binds(result, finding)` says whether a `cns.gate.GateResult` was issued against exactly that finding, using the subject labels `cccb.duplicate` and `cccb.recurrence`. A verdict "these are duplicates" binds to that pair and that measurement; change either text, swap the pair or change a threshold and it does not bind.

**Binding only, and why.** There is no gate, verdict mapping or chain here. CCCb measures and decides nothing; whether a duplicate counts as a new occurrence, or a recurrence may raise an anomaly, is CCC's rule. The `result` in a finding is only whether the measurement cleared its own threshold. `tests/test_cns_connector.py` runs the real `TextMatcher` over real texts and checks the findings agree with what it reports.

## Role in the STACK spine

CCCb is a measurement library, not a spine stage. It is not one of the five
evidence-spine components (HERALD, TIE, Conservation_Kernel,
Governance_Gateway, CCC) and CNS's `chains/evidence_spine.py` does not mention
it. It sits one level below the last of them: CCC (the store that judges an
attempt to ingest) calls CCCb to measure whether a new text overlaps an earlier
one, then applies its own rule to the number.

    HERALD -> TIE -> Conservation_Kernel -> Governance_Gateway -> CCC
                                                                  |
                                          (text_matcher=, injected)
                                                                  v
                                                        CCCb  TextMatcher
                                                        matching + recurrence
                                                                  .
                                    optional, caller-driven       . cns_connector
                                                                  v
                                                    CNS  cns.gate.subject_digest

**Purpose.** Answer two questions about text, deterministically and without
dependencies: is this overlap too long and specific to be coincidence, and do
these texts share enough vocabulary to be the same pattern again.

**Inputs and outputs.** Input: strings (`add(item_id, text)`, then
`duplicate_of(text)` / `recurrence_of(text)`). Output: plain tuples of
`str`, `float`, `int`, or `None`. Indexes live in memory only; a caller that
persists texts feeds them back through `add` after a restart. With the CNS
connector: a frozen `DuplicateFinding` or `RecurrenceFinding` holding SHA-256
of each text, the score, thresholds and a boolean reading.

**Owns.** The two measurements, the thresholds in force (`DUPLICATE_THRESHOLD`
1e-9, `MINIMUM_MATCH_LENGTH` 40, `RECURRENCE_THRESHOLD` 0.5,
`MINIMUM_SIGNATURE_SIZE` 4), the packaged known-boilerplate texts used to
discount licence text, and the shape of a finding.

**Does not own.** Any record or store (CCC). What a match means: whether a
duplicate counts as a new occurrence, whether a recurrence may raise an
anomaly to a pattern, whether anything is ingested (CCC's rule). Truth or
authenticity of a text. Meaning-based similarity (Ecology's `SemanticIndex`
provider, plugged into CCC separately). Admission (Governance_Gateway),
evidence recording (TIE), root-artifact judgement (Conservation_Kernel),
claim extraction (HERALD). A CNS verdict: CCCb never issues a `GateResult`,
and a finding's `result` is only whether the measurement cleared its own
threshold.

**Companions.**
[CCC](https://github.com/wking53214/CCC) depends on CCCb: its
`pyproject.toml` pins `cccb` to commit `8e3c779` (an ancestor of this
branch's base, so it does not include later changes), and `ccc/system.py`
takes the matcher by injection (`text_matcher=None`), never importing CCCb.
[CNS](https://github.com/wking53214/CNS) lists CCCb in
`cns_composition/consumers.py` as an optional connector that loads `cns.gate`
on demand. [Link](https://github.com/wking53214/Link) connects Triad-42, CCC
and CNS; it has no `cccb` reference in its Python or TOML files, so CCCb
reaches it only through CCC. Only CCC, CNS, Link and Ecology were checked for
references; the other spine repositories were not searched.

**CNS interaction: partial.** Implemented: an optional, binding-only
connector that, only when called, imports `cns.gate` (`cccb/cns_connector.py:83`),
hashes a finding with `cns.gate.subject_digest` (`:219`, `:225`) and checks a
`cns.gate.GateResult` against it in `binds` (`:228`, `:245`). Absent: nothing
in the package builds a gate, a verdict mapping or a chain, and nothing in
`cccb/` outside `cns_connector.py` mentions CNS; `TextMatcher` and CCC's call
path (`ccc/system.py:1180`, `:1200`) do not use the connector. Nothing in this
repository or in CCC was found that calls `binds` in a running flow, so the
connector is a tested contract, not an integrated step. There is no UAI-1
(signed message) code here: CCCb runs inside CCC's process and sends nothing
across one.

**Maturity and limitations** (measured 2026-10-31). `python -m pytest -q`
from the repository root with CNS 2.3.0 installed: 122 passed, 0 failed,
0 skipped. Limits: in-memory indexes with no persistence; comparison length is
capped (`MAX_COMPARISON_LENGTH` 50,000 characters); the entropy
figure is a fixed English estimate (1.3 bits per character); shared wording
only, never shared meaning.

## Known gaps

- The recurrence threshold and the duplicate threshold live here with the
  math. CCC owns the decision about what a match means, but not yet these two
  numbers.

## Tests

`pytest`. CI installs the package (not editable) and runs the suite against
the installed copy, so data that fails to ship fails the build.
