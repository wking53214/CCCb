"""The duplicate measurement must not depend on the process's hash seed.

`_matching_spans` walks the shingles two texts share. Which shingle of a repeated passage it meets
first decides where that span starts, so walking them in set order made the same two texts measure
differently from one run to the next (the match length of one pair was 48 in some processes and 45 in
others). Each seed below is a fresh interpreter, because hash order is fixed per process.
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CODE = textwrap.dedent(
    """
    from cccb import matching
    repeated = ("bebhhhgdbhaggahedbfaaa agdga dhh dfddheag bcedeeh gahdggcf fbh bc gfhahaegcc dad  "
                "bebhhhgdbhaggahedbfaaa agdga dhh dfddheag bcebf ")
    single = "bebhhhgdbhaggahedbfaaa agdga dhh dfddheag bcebf g"
    one = matching.anti_probability_of_coincidental_match(repeated, single)
    two = matching.anti_probability_of_coincidental_match(single, repeated)
    print(one.match_length, two.match_length, one.anti_probability, two.anti_probability)
    """
)


def measure(seed: int) -> str:
    env = {"PYTHONPATH": str(ROOT), "PYTHONHASHSEED": str(seed), "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    done = subprocess.run([sys.executable, "-c", CODE], capture_output=True, text=True, env=env, timeout=120)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def test_the_same_two_texts_measure_the_same_under_every_hash_seed():
    results = {seed: measure(seed) for seed in range(12)}
    assert len(set(results.values())) == 1, results


def test_a_text_that_repeats_a_passage_is_measured_differently_from_each_side():
    forward, backward = measure(0).split()[:2]
    assert (forward, backward) == ("48", "45")
