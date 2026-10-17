"""Binding CCCb findings to CNS verdicts: the content, its digest, and ``binds``.

These skip where ``cns`` is not installed. CI installs the extra and sets
CCCB_REQUIRE_CNS=1, so there they cannot skip. The connector is binding only:
nothing here decides whether a duplicate or a recurrence counts.
"""
from __future__ import annotations

import dataclasses
import os

import pytest

if os.environ.get("CCCB_REQUIRE_CNS") == "1":  # CI: a missing cns is a failure, not a skip
    import cns.gate as gate
else:
    gate = pytest.importorskip("cns.gate")

from cccb import TextMatcher, matching, recurrence  # noqa: E402
from cccb.cns_connector import (  # noqa: E402
    DUPLICATE_SUBJECT, RECURRENCE_SUBJECT, DuplicateFinding, RecurrenceFinding, binds, duplicate_content,
    duplicate_digest, duplicate_finding, recurrence_content, recurrence_digest, recurrence_finding)

LONG = ("This exact sentence about the retry path never re-reading the lease "
        "was resubmitted word for word to inflate the anomaly count.")
NEW = "prefix " + LONG + " suffix"
OTHER = "An entirely different note about invoices, due dates and how the quarterly payments were reconciled."
PATTERN = "the governance terminology inflated again into grandiose pseudo-technical jargon"
RECUR = "governance terminology inflated once more, grandiose jargon returning"
UNRELATED = "the vocabulary ballooned pompously once more"
PLAIN = (str, int, float, bool)


def result_for(digest, subject, outcome=None):
    return gate.GateResult(
        gate="other.repo.gate", position=gate.GatePosition.OMEGA,
        outcome=outcome or gate.GateOutcome.PASS, reason="r", subject=subject, subject_digest=digest)


# ------------------------------------------------------------ determinism

def test_the_same_pair_measured_twice_has_the_same_content_and_digest():
    one, two = duplicate_finding(NEW, LONG), duplicate_finding(NEW, LONG)
    assert one is not two and duplicate_content(one) == duplicate_content(two)
    assert duplicate_digest(one) == duplicate_digest(two)
    one, two = recurrence_finding(RECUR, PATTERN), recurrence_finding(RECUR, PATTERN)
    assert recurrence_content(one) == recurrence_content(two)
    assert recurrence_digest(one) == recurrence_digest(two)


def test_digests_are_sha256_hex():
    for digest in (duplicate_digest(duplicate_finding(NEW, LONG)), recurrence_digest(recurrence_finding(RECUR, PATTERN))):
        assert len(digest) == 64 and int(digest, 16) >= 0


# ------------------------------------------------------------ what is bound

def test_the_duplicate_content_names_the_kind_the_pair_the_measurement_the_threshold_and_the_result():
    content = duplicate_content(duplicate_finding(NEW, LONG))
    assert set(content) == {f.name for f in dataclasses.fields(DuplicateFinding)} | {"kind"}
    assert content["kind"] == "duplicate" and content["result"] is True
    assert content["threshold"] == matching.DUPLICATE_THRESHOLD
    assert content["minimum_match_length"] == matching.MINIMUM_MATCH_LENGTH
    assert content["match_length"] >= matching.MINIMUM_MATCH_LENGTH and content["anti_probability"] < content["threshold"]


def test_the_recurrence_content_names_the_kind_the_pair_the_measurement_the_threshold_and_the_result():
    content = recurrence_content(recurrence_finding(RECUR, PATTERN))
    assert set(content) == {f.name for f in dataclasses.fields(RecurrenceFinding)} | {"kind"}
    assert content["kind"] == "recurrence" and content["result"] is True
    assert content["threshold"] == recurrence.RECURRENCE_THRESHOLD
    assert content["minimum_signature_size"] == recurrence.MINIMUM_SIGNATURE_SIZE
    assert content["score"] >= content["threshold"]


def test_the_texts_are_bound_by_hash_not_copied():
    content = duplicate_content(duplicate_finding(NEW, LONG))
    assert len(content["text_a_sha256"]) == 64 and len(content["text_b_sha256"]) == 64
    assert LONG not in repr(content)


def duplicate_base():
    return duplicate_finding(NEW, LONG)


def recurrence_base():
    return recurrence_finding(RECUR, PATTERN)


DUPLICATE_CHANGES = {
    "text a hash": dict(text_a_sha256="0" * 64),
    "text b hash": dict(text_b_sha256="0" * 64),
    "score": dict(anti_probability=1e-8),
    "match length": dict(match_length=1),
    "boilerplate flag": dict(explained_by_known_boilerplate=True),
    "threshold": dict(threshold=1e-6),
    "minimum match length": dict(minimum_match_length=20),
    "result": dict(result=False),
}

RECURRENCE_CHANGES = {
    "text a hash": dict(text_a_sha256="0" * 64),
    "text b hash": dict(text_b_sha256="0" * 64),
    "score": dict(score=0.9),
    "threshold": dict(threshold=0.6),
    "minimum signature size": dict(minimum_signature_size=3),
    "signature size a": dict(signature_size_a=1),
    "signature size b": dict(signature_size_b=1),
    "result": dict(result=False),
}


@pytest.mark.parametrize("name", list(DUPLICATE_CHANGES))
def test_the_duplicate_digest_changes_when_any_bound_field_changes(name):
    base = duplicate_base()
    assert duplicate_digest(dataclasses.replace(base, **DUPLICATE_CHANGES[name])) != duplicate_digest(base)


@pytest.mark.parametrize("name", list(RECURRENCE_CHANGES))
def test_the_recurrence_digest_changes_when_any_bound_field_changes(name):
    base = recurrence_base()
    assert recurrence_digest(dataclasses.replace(base, **RECURRENCE_CHANGES[name])) != recurrence_digest(base)


def test_every_field_of_each_finding_is_exercised_by_a_change():
    assert {k for change in DUPLICATE_CHANGES.values() for k in change} == {f.name for f in dataclasses.fields(DuplicateFinding)}
    assert {k for change in RECURRENCE_CHANGES.values() for k in change} == {f.name for f in dataclasses.fields(RecurrenceFinding)}


def test_the_measurement_kind_is_part_of_what_is_bound():
    base = duplicate_base()
    same_numbers = dict(duplicate_content(base))
    assert same_numbers["kind"] == "duplicate" and gate.subject_digest({**same_numbers, "kind": "recurrence"}) != duplicate_digest(base)


@pytest.mark.parametrize("a, b", [
    (NEW + "!", LONG), (NEW, LONG + "!"), (NEW, OTHER), (OTHER, LONG)])
def test_changing_either_text_changes_the_digest(a, b):
    assert duplicate_digest(duplicate_finding(a, b)) != duplicate_digest(duplicate_finding(NEW, LONG))


@pytest.mark.parametrize("a, b", [
    (RECUR + "!", PATTERN), (RECUR, PATTERN + "!"), (UNRELATED, PATTERN)])
def test_changing_either_text_changes_the_recurrence_digest(a, b):
    assert recurrence_digest(recurrence_finding(a, b)) != recurrence_digest(recurrence_finding(RECUR, PATTERN))


def test_the_pair_is_ordered_because_the_measurement_is_made_in_that_order():
    assert duplicate_digest(duplicate_finding(NEW, LONG)) != duplicate_digest(duplicate_finding(LONG, NEW))
    assert recurrence_digest(recurrence_finding(RECUR, PATTERN)) != recurrence_digest(recurrence_finding(PATTERN, RECUR))


def test_the_duplicate_measurement_itself_depends_on_the_order_of_the_pair():
    """A text that repeats a passage is measured differently from each side, so the order is part of the finding."""
    repeated = ("bebhhhgdbhaggahedbfaaa agdga dhh dfddheag bcedeeh gahdggcf fbh bc gfhahaegcc dad  "
                "bebhhhgdbhaggahedbfaaa agdga dhh dfddheag bcebf ")
    single = "bebhhhgdbhaggahedbfaaa agdga dhh dfddheag bcebf g"
    forward, backward = duplicate_finding(repeated, single), duplicate_finding(single, repeated)
    assert (forward.match_length, backward.match_length) == (48, 45)

    matcher = TextMatcher()
    matcher.add("d1", single)
    assert matcher.duplicate_of(repeated)[1:] == (forward.anti_probability, forward.match_length)


def test_a_changed_threshold_in_force_does_not_carry_a_verdict_over(monkeypatch):
    before = duplicate_digest(duplicate_finding(NEW, LONG))
    monkeypatch.setattr(matching, "DUPLICATE_THRESHOLD", 1e-12)
    assert duplicate_digest(duplicate_finding(NEW, LONG)) != before
    rec_before = recurrence_digest(recurrence_finding(RECUR, PATTERN))
    monkeypatch.setattr(recurrence, "RECURRENCE_THRESHOLD", 0.4)
    assert recurrence_digest(recurrence_finding(RECUR, PATTERN)) != rec_before


# ------------------------------------------------------------ what is not bound

def test_equal_texts_that_are_different_objects_digest_alike():
    assert duplicate_digest(duplicate_finding("".join(list(NEW)), "".join(list(LONG)))) \
        == duplicate_digest(duplicate_finding(NEW, LONG))


# ------------------------------------------------------------ types

@pytest.mark.parametrize("bad", [None, "finding", {"kind": "duplicate"}, 7, recurrence_base()])
def test_a_duplicate_function_rejects_anything_that_is_not_a_duplicate_finding(bad):
    for function in (duplicate_content, duplicate_digest):
        with pytest.raises(TypeError):
            function(bad)


@pytest.mark.parametrize("bad", [None, "finding", {"kind": "recurrence"}, 7, duplicate_base()])
def test_a_recurrence_function_rejects_anything_that_is_not_a_recurrence_finding(bad):
    for function in (recurrence_content, recurrence_digest):
        with pytest.raises(TypeError):
            function(bad)


@pytest.mark.parametrize("bad", [None, "x", {"a": 1}, 7, (1, 2)])
def test_binds_rejects_anything_that_is_not_a_finding(bad):
    with pytest.raises(TypeError):
        binds(result_for("0" * 64, DUPLICATE_SUBJECT), bad)


@pytest.mark.parametrize("bad", [None, b"bytes", 7, ["a"], {"a"}])
def test_measuring_something_that_is_not_text_is_a_type_error(bad):
    for function in (duplicate_finding, recurrence_finding):
        with pytest.raises(TypeError):
            function(bad, "text")
        with pytest.raises(TypeError):
            function("text", bad)


@pytest.mark.parametrize("field, value", [
    ("anti_probability", float("nan")), ("anti_probability", float("inf")), ("threshold", float("-inf")),
    ("match_length", 3.5 + 0j), ("text_a_sha256", None), ("result", object()), ("match_length", [1])])
def test_a_hand_built_finding_with_fields_that_are_not_plain_data_is_a_type_error(field, value):
    broken = dataclasses.replace(duplicate_base(), **{field: value})
    with pytest.raises(TypeError):
        duplicate_content(broken)
    with pytest.raises(TypeError):
        duplicate_digest(broken)


def test_a_non_finite_recurrence_score_is_a_type_error():
    with pytest.raises(TypeError):
        recurrence_content(dataclasses.replace(recurrence_base(), score=float("nan")))


def test_the_content_only_has_types_cns_accepts():
    for content in (duplicate_content(duplicate_base()), recurrence_content(recurrence_base()),
                    duplicate_content(duplicate_finding(NEW, OTHER))):
        assert all(type(k) is str for k in content)
        assert all(type(v) in PLAIN for v in content.values())
        assert gate.subject_digest(content)   # cns itself accepts it


def test_text_with_lone_surrogates_can_still_be_measured_and_bound():
    odd = "caf\udc80 " + LONG
    finding = duplicate_finding(odd, LONG)
    assert len(duplicate_digest(finding)) == 64


# ------------------------------------------------------------ binds

def test_binds_is_true_for_the_duplicate_finding_it_was_issued_against_and_false_for_another():
    finding = duplicate_base()
    result = result_for(duplicate_digest(finding), DUPLICATE_SUBJECT)
    assert result.bound() and binds(result, finding)
    assert binds(result, duplicate_finding(NEW, LONG))
    assert not binds(result, duplicate_finding(NEW, OTHER))
    assert not binds(result, duplicate_finding(LONG, NEW))
    assert not binds(result, duplicate_finding(NEW + "!", LONG))
    assert not binds(result, dataclasses.replace(finding, anti_probability=1e-8))
    assert not binds(result, dataclasses.replace(finding, result=False))


def test_binds_is_true_for_the_recurrence_finding_it_was_issued_against_and_false_for_another():
    finding = recurrence_base()
    result = result_for(recurrence_digest(finding), RECURRENCE_SUBJECT)
    assert binds(result, finding) and binds(result, recurrence_finding(RECUR, PATTERN))
    assert not binds(result, recurrence_finding(UNRELATED, PATTERN))
    assert not binds(result, dataclasses.replace(finding, score=0.99))


def test_binds_checks_the_subject_label():
    finding = duplicate_base()
    wrong = result_for(duplicate_digest(finding), "something.else")
    assert not binds(wrong, finding)
    assert not binds(wrong, finding, subject="")
    assert not binds(wrong, finding, subject=DUPLICATE_SUBJECT)
    assert binds(wrong, finding, subject="something.else")
    right = result_for(duplicate_digest(finding), DUPLICATE_SUBJECT)
    assert not binds(right, finding, subject="something.else")


def test_a_duplicate_verdict_does_not_bind_to_a_recurrence_finding_or_back():
    dup, rec = duplicate_base(), recurrence_base()
    assert not binds(result_for(duplicate_digest(dup), DUPLICATE_SUBJECT), rec)
    assert not binds(result_for(recurrence_digest(rec), RECURRENCE_SUBJECT), dup)
    # even with the right digest, the label keeps the two apart
    assert not binds(result_for(recurrence_digest(rec), DUPLICATE_SUBJECT), rec)
    assert not binds(result_for(duplicate_digest(dup), RECURRENCE_SUBJECT), dup)


def test_an_unbound_or_hand_built_result_binds_to_nothing():
    finding = duplicate_base()
    bare = gate.GateResult(gate="g", position=gate.GatePosition.ALPHA, outcome=gate.GateOutcome.PASS)
    assert not bare.bound() and not binds(bare, finding) and not binds(bare, finding, subject="")
    no_digest = gate.GateResult(gate="g", position=gate.GatePosition.ALPHA, outcome=gate.GateOutcome.PASS,
                                subject=DUPLICATE_SUBJECT)
    assert not binds(no_digest, finding)
    no_subject = gate.GateResult(gate="g", position=gate.GatePosition.ALPHA, outcome=gate.GateOutcome.PASS,
                                 subject_digest=duplicate_digest(finding))
    assert not binds(no_subject, finding)


@pytest.mark.parametrize("impostor", [None, "pass", {"subject": DUPLICATE_SUBJECT}, object()])
def test_something_that_is_not_a_gate_result_binds_to_nothing(impostor):
    assert binds(impostor, duplicate_base()) is False


def test_an_impostor_that_claims_to_bind_is_not_believed():
    class Liar:
        def binds(self, subject, digest):
            return True

    assert binds(Liar(), duplicate_base()) is False


@pytest.mark.parametrize("outcome", list(gate.GateOutcome))
def test_binding_does_not_depend_on_the_verdict(outcome):
    finding = duplicate_base()
    assert binds(result_for(duplicate_digest(finding), DUPLICATE_SUBJECT, outcome), finding)


# ------------------------------------------------------------ against CCCb's own TextMatcher

def test_a_duplicate_found_by_the_real_matcher_binds_to_exactly_that_pair():
    matcher = TextMatcher()
    matcher.add("d1", LONG)
    item_id, anti_probability, match_length = matcher.duplicate_of(NEW)
    assert item_id == "d1"

    finding = duplicate_finding(NEW, LONG)
    assert (finding.anti_probability, finding.match_length) == (anti_probability, match_length)
    assert finding.result is True and finding.threshold == matching.DUPLICATE_THRESHOLD

    verdict = result_for(duplicate_digest(finding), DUPLICATE_SUBJECT)
    assert binds(verdict, duplicate_finding(NEW, LONG))
    assert not binds(verdict, duplicate_finding(NEW, OTHER))
    assert not binds(verdict, duplicate_finding("different " + LONG[:60], LONG))


@pytest.mark.parametrize("text", [NEW, LONG, "the retry path", OTHER, "", LONG[:30] + OTHER])
def test_the_finding_agrees_with_the_real_matcher_on_whether_it_is_a_duplicate(text):
    matcher = TextMatcher()
    matcher.add("d1", LONG)
    hit = matcher.duplicate_of(text)
    finding = duplicate_finding(text, LONG)
    assert finding.result is (hit is not None)
    if hit is not None:
        assert (finding.anti_probability, finding.match_length) == hit[1:]


def test_a_recurrence_found_by_the_real_matcher_binds_to_exactly_that_pair():
    matcher = TextMatcher()
    matcher.add("d1", PATTERN)
    best_id, best_score, matches = matcher.recurrence_of(RECUR)
    assert best_id == "d1" and matches == (("d1", best_score),)

    finding = recurrence_finding(RECUR, PATTERN)
    assert finding.score == best_score and finding.result is True

    verdict = result_for(recurrence_digest(finding), RECURRENCE_SUBJECT)
    assert binds(verdict, recurrence_finding(RECUR, PATTERN))
    assert not binds(verdict, recurrence_finding(UNRELATED, PATTERN))


@pytest.mark.parametrize("text", [RECUR, UNRELATED, PATTERN, "alpha beta gamma", "", OTHER])
def test_the_finding_agrees_with_the_real_matcher_on_whether_it_is_a_recurrence(text):
    matcher = TextMatcher()
    matcher.add("d1", PATTERN)
    hit = matcher.recurrence_of(text)
    finding = recurrence_finding(text, PATTERN)
    assert finding.result is (hit is not None)
    if hit is not None:
        assert finding.score == hit[1]


def test_two_identical_texts_with_too_small_a_signature_are_not_a_recurrence_and_the_finding_says_so():
    short = "alpha beta gamma"
    matcher = TextMatcher()
    matcher.add("d1", short)
    assert matcher.recurrence_of(short) is None
    finding = recurrence_finding(short, short)
    assert finding.score == 1.0 and finding.signature_size_a == 3 and finding.result is False


def test_a_finding_that_did_not_clear_the_threshold_is_still_a_finding_and_binds():
    finding = duplicate_finding("hello there", "hello world")
    assert finding.result is False
    assert binds(result_for(duplicate_digest(finding), DUPLICATE_SUBJECT), finding)
    miss = recurrence_finding(UNRELATED, PATTERN)
    assert miss.result is False
    assert binds(result_for(recurrence_digest(miss), RECURRENCE_SUBJECT), miss)
    assert recurrence_digest(miss) != recurrence_digest(recurrence_base())
