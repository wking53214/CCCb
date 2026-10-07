"""Recurrence detection math: concept-signature overlap between two texts.

Moved from CCC (wking53214/CCC tests/test_recurrence.py at d039efd). The tests
that drive CCC's anomaly -> pattern -> mandate ladder with this detector stayed
in CCC; these are the ones that test the detector alone.
"""
from __future__ import annotations

from cccb.recurrence import RecurrenceDetector


# --- the detector itself ------------------------------------------------

def test_shared_vocabulary_is_a_recurrence_different_words_are_not():
    d = RecurrenceDetector()
    d.register("d1", "the governance terminology inflated again into grandiose pseudo-technical jargon")
    # shares "governance terminology inflated grandiose jargon" -> recurrence
    hit = d.find_recurrence("governance terminology inflated once more, grandiose jargon returning")
    assert hit is not None and hit[0] == "d1"
    # same idea, no shared significant words -> not detected (stated limit)
    miss = d.find_recurrence("the vocabulary ballooned pompously once more")
    assert miss is None


def test_a_signature_below_minimum_size_never_matches():
    d = RecurrenceDetector()
    d.register("d1", "alpha beta gamma delta epsilon zeta")
    assert d.find_recurrence("alpha beta gamma") is None  # 3 concepts < MINIMUM_SIGNATURE_SIZE


def test_index_only_compares_against_discoveries_sharing_a_concept():
    d = RecurrenceDetector()
    for i in range(500):
        d.register(f"unrelated{i}", f"completely distinct topic number {i} about widgets and sprockets {i}")
    d.register("target", "governance terminology inflation grandiose jargon escalation arc")
    hit = d.find_recurrence("governance terminology inflation grandiose jargon returning again")
    assert hit is not None and hit[0] == "target"
