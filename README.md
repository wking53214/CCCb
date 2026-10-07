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

## Known gaps

- `tests/test_smash_findings.py` reads a license file from `~/HERALD/LICENSE`
  and returns early, passing without checking anything, when that file is
  absent. CI never has it, so two of its tests verify nothing there. Carried
  over unchanged from CCC; not yet fixed.
- The recurrence threshold and the duplicate threshold live here with the
  math. CCC owns the decision about what a match means, but not yet these two
  numbers.

## Tests

`pytest`. CI installs the package (not editable) and runs the suite against
the installed copy, so data that fails to ship fails the build.
