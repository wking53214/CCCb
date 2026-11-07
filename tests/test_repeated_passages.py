"""Adversarial checks for repeated, reordered, and overlapping passages.

The matcher indexes each 40-character chunk by its first position only. These
tests check that the longest genuine overlap is still reported when the same
chunk appears more than once, in either text, with different surroundings.

Each expected length is checked against a brute-force longest-common-substring
calculation, so the tests do not depend on how the matcher is written.
"""
from __future__ import annotations

import random

from cccb.matching import MINIMUM_MATCH_LENGTH, anti_probability_of_coincidental_match

ALPHABET = "abcdefghijklmnopqrstuvwxyz ."


def _rand(n: int, rng: random.Random) -> str:
    return "".join(rng.choice(ALPHABET) for _ in range(n))


def _longest_common_substring(a: str, b: str) -> int:
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def _reported(a: str, b: str) -> int:
    return anti_probability_of_coincidental_match(a, b).match_length


def test_passage_also_appears_earlier_in_the_other_text():
    rng = random.Random(101)
    passage = _rand(220, rng)
    a = passage
    b = _rand(90, rng) + passage[:60] + _rand(40, rng) + passage + _rand(30, rng)
    assert _reported(a, b) >= len(passage)


def test_repeated_block_in_first_text_with_different_continuations():
    rng = random.Random(202)
    block = _rand(70, rng)
    real_copy = block + _rand(180, rng)
    decoy = block + _rand(50, rng)
    a = decoy + _rand(30, rng) + real_copy
    b = real_copy
    assert _reported(a, b) >= len(real_copy)


def test_reordered_passages_still_report_the_longest_overlap():
    rng = random.Random(303)
    p1 = _rand(150, rng)
    p2 = _rand(200, rng)
    a = p1 + _rand(20, rng) + p2
    b = p2 + _rand(20, rng) + p1
    assert _reported(a, b) >= max(len(p1), len(p2))


def test_overlapping_passages_report_the_shared_stretch():
    rng = random.Random(404)
    source = _rand(260, rng)
    a = source[:170]
    b = source[120:]
    shared = _longest_common_substring(a, b)
    assert shared >= 50
    assert _reported(a, b) >= shared


def test_seeded_cases_match_brute_force_longest_overlap():
    """A bounded, seeded sweep: the reported overlap must never be shorter
    than the true longest shared stretch when that stretch is long enough
    to count."""
    rng = random.Random(505)
    for _ in range(120):
        block = _rand(rng.randint(41, 70), rng)
        a = _rand(rng.randint(0, 60), rng) + block + _rand(rng.randint(0, 60), rng) + block + _rand(rng.randint(0, 40), rng)
        b = _rand(rng.randint(0, 60), rng) + block + _rand(rng.randint(0, 80), rng)
        truth = _longest_common_substring(a, b)
        if truth >= MINIMUM_MATCH_LENGTH:
            assert _reported(a, b) >= truth, (truth, a, b)
