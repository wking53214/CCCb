"""Optional connector to CNS (``cns.gate``): binding only.

CCCb is independent. It has no runtime dependency, imports nothing from CNS
when it loads (and nothing from CCC, ever), and its whole suite passes with CNS
absent. This module is the one place that knows CNS exists, and it asks for CNS
only when a function that needs it is called. Without CNS installed those calls
raise :class:`CnsNotInstalled` with the install command; nothing else in CCCb
is affected, and the ``*_content`` and ``*_finding`` functions work without CNS
at all.

What connecting means
---------------------
CNS's shared gate contract carries, on every verdict, the subject it judged and
a digest of the content it judged (``GateResult.subject``,
``GateResult.subject_digest``). This module lets one measurement of one pair of
texts be named that way, so a verdict such as "these are duplicates" can be
checked against exactly that pair and exactly that measurement with
``GateResult.binds``.

That is all it does. CCCb measures; it does not decide. Whether a duplicate
counts as a new occurrence, or a recurrence may raise an anomaly, is CCC's rule,
so there is no gate here, no verdict mapping and no chain, and the ``result``
recorded in a finding is the measurement's own reading (it cleared the
threshold or it did not), not a decision.

What is bound
-------------
A finding is one measurement of an ordered pair ``(text_a, text_b)``, the way
``TextMatcher`` makes it (``text_a`` is the new text, ``text_b`` the earlier
one it was compared with):

* :func:`duplicate_finding` runs ``cccb.matching`` over the pair.
* :func:`recurrence_finding` runs ``cccb.recurrence`` over the pair.

Each finding holds the SHA-256 of each text (the texts themselves are not
copied), the measurement kind, the score, the threshold and minimum in force,
and the result. Change a text, swap the pair, or change a threshold and the
digest changes, so a verdict does not carry over.

Install with the extra: ``pip install 'cccb[cns]'``.
"""

from __future__ import annotations

import hashlib
import importlib
import math
from dataclasses import dataclass
from types import ModuleType
from typing import Optional

from . import matching, recurrence

__all__ = [
    "CnsNotInstalled",
    "DUPLICATE_SUBJECT",
    "DuplicateFinding",
    "RECURRENCE_SUBJECT",
    "RecurrenceFinding",
    "binds",
    "cns_available",
    "duplicate_content",
    "duplicate_digest",
    "duplicate_finding",
    "recurrence_content",
    "recurrence_digest",
    "recurrence_finding",
]

INSTALL_HINT = "pip install 'cccb[cns]'"

DUPLICATE_SUBJECT = "cccb.duplicate"
RECURRENCE_SUBJECT = "cccb.recurrence"


class CnsNotInstalled(ImportError):
    """Raised by this module's functions when ``cns`` cannot be imported."""


def _cns_gate() -> ModuleType:
    """Import ``cns.gate`` on demand, or say exactly what is missing."""
    try:
        return importlib.import_module("cns.gate")
    except ImportError as exc:
        raise CnsNotInstalled(
            "cccb.cns_connector needs the CNS package (cns.gate), which is not "
            f"installed. Install it with: {INSTALL_HINT}. CCCb itself works "
            "without it."
        ) from exc


def cns_available() -> bool:
    """Whether the CNS gate contract can be imported in this environment."""
    try:
        _cns_gate()
    except CnsNotInstalled:
        return False
    return True


@dataclass(frozen=True)
class DuplicateFinding:
    """One duplicate measurement of the pair ``(text_a, text_b)``."""

    text_a_sha256: str
    text_b_sha256: str
    anti_probability: float
    match_length: int
    explained_by_known_boilerplate: bool
    threshold: float
    minimum_match_length: int
    result: bool


@dataclass(frozen=True)
class RecurrenceFinding:
    """One recurrence measurement of the pair ``(text_a, text_b)``."""

    text_a_sha256: str
    text_b_sha256: str
    score: float
    threshold: float
    minimum_signature_size: int
    signature_size_a: int
    signature_size_b: int
    result: bool


def _sha256(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError(f"a text is expected here; got {type(text).__name__}")
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def duplicate_finding(text_a: str, text_b: str) -> DuplicateFinding:
    """Measure the pair the way ``TextMatcher.duplicate_of`` measures a new text against an earlier one."""
    digests = (_sha256(text_a), _sha256(text_b))
    measured = matching.anti_probability_of_coincidental_match(text_a, text_b)
    return DuplicateFinding(
        text_a_sha256=digests[0],
        text_b_sha256=digests[1],
        anti_probability=measured.anti_probability,
        match_length=measured.match_length,
        explained_by_known_boilerplate=measured.explained_by_known_boilerplate,
        threshold=matching.DUPLICATE_THRESHOLD,
        minimum_match_length=matching.MINIMUM_MATCH_LENGTH,
        result=measured.implausible_as_coincidence,
    )


def recurrence_finding(text_a: str, text_b: str) -> RecurrenceFinding:
    """Measure the pair the way ``TextMatcher.recurrence_of`` measures a new text against an earlier one."""
    digests = (_sha256(text_a), _sha256(text_b))
    signature_a, signature_b = recurrence.concept_set(text_a), recurrence.concept_set(text_b)
    detector = recurrence.RecurrenceDetector()
    detector.register("b", text_b)
    return RecurrenceFinding(
        text_a_sha256=digests[0],
        text_b_sha256=digests[1],
        score=recurrence._jaccard(signature_a, signature_b),
        threshold=recurrence.RECURRENCE_THRESHOLD,
        minimum_signature_size=recurrence.MINIMUM_SIGNATURE_SIZE,
        signature_size_a=len(signature_a),
        signature_size_b=len(signature_b),
        result=detector.find_recurrence(text_a) is not None,
    )


def _require(obj: object, kind: type) -> None:
    if not isinstance(obj, kind):
        raise TypeError(f"a {kind.__name__} is expected here; got {type(obj).__name__}")


def _checked(content: dict) -> dict:
    """Refuse a hand-built finding whose fields are not plain data CNS can bind."""
    for name, value in content.items():
        if type(value) not in (str, int, float, bool):
            raise TypeError(f"{name} must be a string, number or bool to be bound; got {type(value).__name__}")
        if isinstance(value, float) and not math.isfinite(value):
            raise TypeError("cannot bind a verdict to NaN or an infinity")
    return content


def duplicate_content(finding: DuplicateFinding) -> dict:
    """The content a verdict on ``finding`` is bound to (plain data, no CNS needed)."""
    _require(finding, DuplicateFinding)
    return _checked({
        "kind": "duplicate",
        "text_a_sha256": finding.text_a_sha256,
        "text_b_sha256": finding.text_b_sha256,
        "anti_probability": finding.anti_probability,
        "match_length": finding.match_length,
        "explained_by_known_boilerplate": finding.explained_by_known_boilerplate,
        "threshold": finding.threshold,
        "minimum_match_length": finding.minimum_match_length,
        "result": finding.result,
    })


def recurrence_content(finding: RecurrenceFinding) -> dict:
    """The content a verdict on ``finding`` is bound to (plain data, no CNS needed)."""
    _require(finding, RecurrenceFinding)
    return _checked({
        "kind": "recurrence",
        "text_a_sha256": finding.text_a_sha256,
        "text_b_sha256": finding.text_b_sha256,
        "score": finding.score,
        "threshold": finding.threshold,
        "minimum_signature_size": finding.minimum_signature_size,
        "signature_size_a": finding.signature_size_a,
        "signature_size_b": finding.signature_size_b,
        "result": finding.result,
    })


def duplicate_digest(finding: DuplicateFinding) -> str:
    """The digest a verdict bound to ``finding`` carries, with ``DUPLICATE_SUBJECT``."""
    content = duplicate_content(finding)
    return _cns_gate().subject_digest(content)


def recurrence_digest(finding: RecurrenceFinding) -> str:
    """The digest a verdict bound to ``finding`` carries, with ``RECURRENCE_SUBJECT``."""
    content = recurrence_content(finding)
    return _cns_gate().subject_digest(content)


def binds(result: object, finding: object, *, subject: Optional[str] = None) -> bool:
    """Whether ``result`` is a CNS verdict issued against exactly ``finding``.

    ``finding`` is a ``DuplicateFinding`` (default subject ``DUPLICATE_SUBJECT``)
    or a ``RecurrenceFinding`` (default ``RECURRENCE_SUBJECT``). An unbound or
    hand-built result, anything that is not a ``cns.gate.GateResult``, a
    different subject label, or a verdict about a different finding is ``False``.
    """
    if isinstance(finding, DuplicateFinding):
        label, digest = DUPLICATE_SUBJECT, duplicate_digest
    elif isinstance(finding, RecurrenceFinding):
        label, digest = RECURRENCE_SUBJECT, recurrence_digest
    else:
        raise TypeError(
            f"a DuplicateFinding or a RecurrenceFinding is expected here; got {type(finding).__name__}"
        )
    computed = digest(finding)
    if not isinstance(result, _cns_gate().GateResult):
        return False
    return bool(result.binds(label if subject is None else subject, computed))
