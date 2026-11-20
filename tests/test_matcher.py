"""TextMatcher, the plug CCC takes, and the package's standing promises."""
from __future__ import annotations

import ast
from pathlib import Path

import cccb
from cccb import TextMatcher
from cccb import matching

LONG = ("This exact sentence about the retry path never re-reading the lease "
        "was resubmitted word for word to inflate the anomaly count.")
PATTERN = "the governance terminology inflated again into grandiose pseudo-technical jargon"
RECUR = "governance terminology inflated once more, grandiose jargon returning"


def test_duplicate_is_reported_with_plain_values():
    m = TextMatcher()
    m.add("d1", LONG)
    hit = m.duplicate_of("prefix " + LONG + " suffix")
    assert hit is not None
    item_id, anti_probability, match_length = hit
    assert item_id == "d1"
    assert isinstance(anti_probability, float) and anti_probability < matching.DUPLICATE_THRESHOLD
    assert isinstance(match_length, int) and match_length >= matching.MINIMUM_MATCH_LENGTH


def test_short_overlap_is_not_a_duplicate():
    m = TextMatcher()
    m.add("d1", LONG)
    assert m.duplicate_of("the retry path") is None


def test_nothing_added_means_nothing_matches():
    m = TextMatcher()
    assert m.duplicate_of(LONG) is None
    assert m.recurrence_of(RECUR) is None


def test_recurrence_returns_best_and_whole_cluster():
    m = TextMatcher()
    m.add("d1", PATTERN)
    best_id, best_score, matches = m.recurrence_of(RECUR)
    assert best_id == "d1" and 0.0 < best_score <= 1.0
    assert matches[0] == ("d1", best_score)


def test_matchers_do_not_share_state():
    a, b = TextMatcher(), TextMatcher()
    a.add("d1", LONG)
    assert b.duplicate_of(LONG) is None


def test_known_boilerplate_ships_and_loads():
    """Inside CCC this data was not declared as package data, so an installed
    (non-editable) copy silently matched with no boilerplate list. Here it is
    declared, and this fails if it ever goes missing again."""
    assert len(matching._KNOWN_BOILERPLATE) >= 2


def test_imports_nothing_from_ccc():
    for path in Path(cccb.__file__).parent.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            for name in names:
                assert name.split(".")[0] != "ccc", f"{path.name} imports {name}"


# The cut-offs: the defaults are unchanged, and a caller that owns the decision can set its own.

def test_the_cutoffs_default_to_the_module_values_and_can_be_read_back():
    m = TextMatcher()
    assert m.duplicate_threshold == matching.DUPLICATE_THRESHOLD
    assert m.recurrence_threshold == cccb.RECURRENCE_THRESHOLD


def test_a_stricter_duplicate_cutoff_turns_a_match_into_no_match():
    m = TextMatcher(duplicate_threshold=1e-300)
    m.add("d1", LONG)
    assert m.duplicate_threshold == 1e-300
    assert m.duplicate_of("prefix " + LONG + " suffix") is None


def test_a_looser_duplicate_cutoff_keeps_a_match_that_the_default_also_finds():
    m = TextMatcher(duplicate_threshold=1e-3)
    m.add("d1", LONG)
    assert m.duplicate_of("prefix " + LONG + " suffix")[0] == "d1"


def test_a_higher_recurrence_cutoff_drops_a_match_a_lower_one_keeps():
    low, high = TextMatcher(recurrence_threshold=0.1), TextMatcher(recurrence_threshold=1.0)
    for m in (low, high):
        m.add("d1", PATTERN)
    assert low.recurrence_of(RECUR) is not None
    assert high.recurrence_of(RECUR) is None


def test_a_bad_cutoff_is_refused_not_clamped():
    import pytest
    for bad in (0, -0.1, 1.5, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            TextMatcher(duplicate_threshold=bad)
        with pytest.raises(ValueError):
            TextMatcher(recurrence_threshold=bad)
    for bad in ("0.5", True, [0.5]):
        with pytest.raises(TypeError):
            TextMatcher(duplicate_threshold=bad)
