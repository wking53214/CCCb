"""Manual sweep behind the repeated-passage claim in docs/STATUS.md.

Not part of the test suite (it runs about 4,500 cases and is too slow for CI).
Run it from the repository root:

    python scripts/repeated_passage_sweep.py

It generates random texts with repeated and decoy passages, compares each
reported overlap against a brute-force longest-common-substring calculation,
and reports how many cases the matcher reported shorter than the true value,
and by how much at most.

Expected result: 0 of 4,500 cases are short. Before the alignment fix, the
matcher aligned a repeated chunk only at its first position, and 1 case was 1
character short (see docs/STATUS.md). The fixed case is a regression test in
tests/test_repeated_passages.py.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cccb.matching import anti_probability_of_coincidental_match  # noqa: E402

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


def _check(a: str, b: str, min_truth: int) -> int:
    """Shortfall in characters (0 when the report is not short)."""
    truth = _longest_common_substring(a, b)
    if truth < min_truth:
        return 0
    return max(0, truth - _reported(a, b))


def _sweep_shared_block(seed: int, trials: int) -> tuple[int, int, int]:
    """A shared block repeats in one text; the other text holds one copy."""
    rng = random.Random(seed)
    short = 0
    worst = 0
    for _ in range(trials):
        block = _rand(60, rng)
        a = _rand(rng.randint(0, 120), rng) + block + _rand(rng.randint(0, 120), rng) + block + _rand(rng.randint(0, 80), rng)
        b = _rand(rng.randint(0, 80), rng) + block + _rand(rng.randint(0, 80), rng)
        gap = _check(a, b, 40)
        if gap:
            short += 1
            worst = max(worst, gap)
    return trials, short, worst


def _sweep_decoy_continuations(seed: int, trials: int) -> tuple[int, int, int]:
    """A shared prefix repeats in one text with different continuations; the
    other text holds one of them."""
    rng = random.Random(seed)
    short = 0
    worst = 0
    for _ in range(trials):
        prefix = _rand(rng.randint(41, 90), rng)
        real_tail = _rand(rng.randint(60, 200), rng)
        decoy = prefix + _rand(rng.randint(5, 80), rng)
        real = prefix + real_tail
        a = _rand(rng.randint(0, 60), rng) + decoy + _rand(rng.randint(0, 40), rng) + real + _rand(rng.randint(0, 40), rng)
        b = _rand(rng.randint(0, 60), rng) + real + _rand(rng.randint(0, 60), rng)
        gap = _check(a, b, 1)
        if gap:
            short += 1
            worst = max(worst, gap)
    return trials, short, worst


def main() -> int:
    total = 0
    short_total = 0
    worst_overall = 0
    for name, run in (
        ("shared block repeated in one text", lambda: _sweep_shared_block(1, 3000)),
        ("decoy continuations", lambda: _sweep_decoy_continuations(7, 1500)),
    ):
        trials, short, worst = run()
        total += trials
        short_total += short
        worst_overall = max(worst_overall, worst)
        print(f"{name}: {trials} cases, {short} reported shorter, worst shortfall {worst} characters")
    print(f"total: {total} cases, {short_total} reported shorter, worst shortfall {worst_overall} characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
