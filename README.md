# CCCb

Measures how alike two pieces of text are. It does not decide what that similarity means.

CCCb is part of ≡TACK, the whole library of repositories this project belongs to. It is a plug-in for [CCC](https://github.com/wking53214/CCC) (the Cognitive Continuity Constitution), the repo that keeps records and decides what a match means.

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

## Role Within ≡TACK

- **What it is.** A text similarity measurement plug-in for CCC.
- **Authority matrix.** Evaluation, including the yes or no. Each of the two deterministic measures (duplicate and recurrence) ends in a cut-off that is fixed in this package (see "Settings in force"): `duplicate_of` and `recurrence_of` return a match, or `None`. CCC acts on that answer and holds no duplicate or recurrence number of its own, so where the line falls is set here, not in CCC (INSPECTED 2026-11-17 in CCC `2379de8`, `ccc/system.py`). CCCb keeps no records: its indexes hold the texts a caller adds, in memory only. It does not enforce, authorize, authenticate or define policy beyond those cut-offs. Its optional CNS connector only builds a bindable finding.
- **Does not own.** What a match means (CCC), or the verdict (CNS binds it).
- **Depends on.** The standard library. CNS is an optional extra.
- **Depended on by.** CCC (optional `match` extra), Link (optional `match` extra), observe-perceive (its `chain` extra, used by its CCC adapter), and CNS (optional connector). The three that pin CCCb pin three different commits. See the table below (re-checked 2026-11-17).
- **Fail behavior.** Without CNS, asking for a digest raises `CnsNotInstalled`. The duplicate measure is easy to slip past (case, spacing, short spans), and a match does not prove a text is genuine.

EXECUTED 2026-11-17 at `5d27a12`, Python 3.13, in two fresh environments. With only this package and pytest installed (the command in "Tests"): 36 passed, 1 skipped (the connector test file, which needs CNS). With the `cns` extra installed and `CCCB_REQUIRE_CNS=1`, the way CI's second job runs: 129 passed, 0 skipped, at the pinned CNS v4.0.0 and at v4.1.0. `ruff check .` is clean with the CI's ruff version. The manual sweep script: 0 of 4,500 cases short. The 129 recorded here on 2026-11-15 is the second figure. Not run: GitHub CI, Python 3.11 and 3.12.

## Where this fits in ≡TACK

CCCb is a shared library, not a stage in any chain. In the evidence spine (the chain below) it serves one stage, CCC.

    HERALD --> TIE --> Conservation_Kernel --> Governance_Gateway --> CCC
                                                                       ^
                                                      CCCb plugs in here, from outside

- **The spine.** HERALD reads a document and extracts claims. TIE records them as evidence. Conservation_Kernel checks the transformation. Governance_Gateway checks admission. CCC judges whether the claim enters its store. CNS composes the chain and decides nothing. CCC's README owns this diagram.
- **Three jobs.** CCC decides what a match means. CCCb measures how alike two texts are. CNS binds a verdict to the content it judged.
- **Not a spine repo.** CNS's spine script does not mention CCCb, and none of HERALD, Conservation_Kernel or Governance_Gateway references it.

Who uses it (re-checked 2026-11-17 against each repo's main; CCCb main is `5d27a12`):

| Repo | How it uses CCCb |
|---|---|
| [CCC](https://github.com/wking53214/CCC) | Optional `match` extra, pinned to `737cf0e`, 8 commits behind main. Since that commit the package differs by one comment line; the rest is docs, the CNS pin and two one-line test edits. Runtime code never imports CCCb; 11 test files do. |
| [Link](https://github.com/wking53214/Link) | Optional `match` extra, pinned to older `8e3c779`, 26 commits behind main and before the alignment fix. One module (`link/calibration.py`) and two test files import it. |
| [observe-perceive](https://github.com/wking53214/observe-perceive) | Its `chain` extra pins `2391191`, 38 commits behind main. Its CCC adapter uses a sibling `CCCb` folder first when one exists, and the installed pin otherwise. |
| [CNS](https://github.com/wking53214/CNS) | Lists CCCb as an optional connector that loads `cns.gate` on demand. The spine script does not call it. |

## Using it with CCC

    from ccc import CCCSystem
    from cccb import TextMatcher

    system = CCCSystem(
        text_matcher=TextMatcher(),
        allow_unguarded_writes=True,    # demo only
        allow_unverified_humans=True,   # demo only
    )

Since CCC's guard change (2026-11-14), `CCCSystem(text_matcher=TextMatcher())` alone raises `UnguardedSystemError` (EXECUTED 2026-11-17 against CCC `2379de8`). The two flags switch CCC's guards off for a demo. A real application passes a `write_permission` and a `human_verifier` in their place; see CCC's README.

CCCb was split out of CCC at commit `d039efd`. Full history is in CCC's git log.

## What it does not do

- It stores no records and does not decide what a match leads to. Whether a duplicate counts as a new occurrence, or a recurrence may raise an anomaly, is CCC's rule. The yes or no itself is made here, against the fixed numbers in "Settings in force", and CCC does not re-check it.
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

CCCb runs without CNS. To use the connector, install the extra from a clone with `pip install '.[cns]'`, or from GitHub with `pip install "cccb[cns] @ git+https://github.com/wking53214/CCCb.git"`. The short form `pip install 'cccb[cns]'`, which the connector's own error message prints, does not work: no package named `cccb` is published on the package index (EXECUTED 2026-11-17). The extra pins CNS to the tag `v4.0.0`. Without CNS, asking for a digest raises `CnsNotInstalled` and nothing else changes.

The connector (`cccb/cns_connector.py`) is the only place that knows CNS exists. It builds a finding for an ordered pair of texts: a hash of each text (the texts are not copied), the score, the thresholds in force, and whether the measurement cleared its threshold. A finding can be digested with CNS, and `binds` checks that a CNS gate result carries the same subject and digest as that finding. Change either text, swap the pair, or change a threshold, and the binding fails. Binding does not prove who issued the result, that it passed, or that anything was authorized.

CNS's side of the seam is `cns_composition/consumers.py`, named in CNS's connection list (`contracts/cns-links.json`), where CCCb is listed as two-way (checked 2026-11-10 at CNS `03eca66`).

The connector does not build gates, verdicts, or chains. It is a tested contract. No running flow in CCC or CNS calls `binds` from this package yet. (CCC calls its own verdict-binding method, which is a different function.)

Current status and test results are in [docs/STATUS.md](docs/STATUS.md).

## Tests

Run `pytest` from the repository root. Tests that need CNS skip when it is not installed. In CI, the CNS job installs the extra and fails instead of skipping. Lint runs with ruff.

## License

Apache-2.0, copyright 2026 William N. King. See `LICENSE` and `NOTICE`.
