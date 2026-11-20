"""The plug CCC takes: one object that measures how alike two texts are.

CCC declares what it needs (``ccc.text_matching.TextMatcher``) and this
satisfies it by shape, without importing CCC. CCC owns what a match means; this
owns only the measurement:

* ``add(item_id, text)`` remembers a text so later texts can be compared to it.
* ``duplicate_of(text)`` returns ``(item_id, anti_probability, match_length)``
  for the strongest earlier text whose overlap with this one is implausible as
  coincidence (see ``cccb.matching``), or ``None``.
* ``recurrence_of(text)`` returns ``(best_id, best_score, matches)`` for earlier
  texts sharing enough significant vocabulary to be the same pattern (see
  ``cccb.recurrence``), or ``None``. ``matches`` is every
  ``(item_id, score)`` at or above the threshold, strongest first.

Everything returned is a plain string, float or int, so a caller needs nothing
from this package to read it. The indexes live in memory; a caller that
persists its texts feeds them back through ``add`` after a restart.
"""

from __future__ import annotations

import math
from typing import Optional

from . import matching, recurrence
from .recurrence import RecurrenceDetector

__all__ = ["TextMatcher"]


def _checked_cutoff(value: Optional[float], name: str) -> Optional[float]:
    """None, or a finite number above 0 and at most 1. Anything else is refused, not clamped."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number or None; got {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number) or not 0.0 < number <= 1.0:
        raise ValueError(f"{name} must be a finite number above 0 and at most 1; got {value!r}")
    return number


class TextMatcher:
    """Duplicate and recurrence measurement over the texts it has been given.

    The two cut-offs default to ``matching.DUPLICATE_THRESHOLD`` and
    ``recurrence.RECURRENCE_THRESHOLD``. A caller that owns the decision (CCC)
    can pass its own, and can read back what is in force from
    ``duplicate_threshold`` and ``recurrence_threshold``.
    """

    def __init__(self, duplicate_threshold: Optional[float] = None,
                 recurrence_threshold: Optional[float] = None) -> None:
        self._duplicate_threshold = _checked_cutoff(duplicate_threshold, "duplicate_threshold")
        self._recurrence_threshold = _checked_cutoff(recurrence_threshold, "recurrence_threshold")
        self._shingles = matching.ShingleIndex()
        self._recurrence = RecurrenceDetector(self._recurrence_threshold)

    @property
    def duplicate_threshold(self) -> float:
        """The anti-probability below which two overlapping texts count as a duplicate."""
        if self._duplicate_threshold is None:
            return matching.DUPLICATE_THRESHOLD
        return self._duplicate_threshold

    @property
    def recurrence_threshold(self) -> float:
        """The overlap at or above which two texts count as the same pattern."""
        if self._recurrence_threshold is None:
            return recurrence.RECURRENCE_THRESHOLD
        return self._recurrence_threshold

    def add(self, item_id: str, text: str) -> None:
        self._shingles.add(item_id, text)
        self._recurrence.register(item_id, text)

    def duplicate_of(self, text: str) -> Optional[tuple[str, float, int]]:
        candidates = self._shingles.candidates_for(text)
        match = matching.best_match_against(text, candidates)
        if match is None or not match[1].implausible_at(self.duplicate_threshold):
            return None
        item_id, result = match
        return (item_id, result.anti_probability, result.match_length)

    def recurrence_of(
        self, text: str
    ) -> Optional[tuple[str, float, tuple[tuple[str, float], ...]]]:
        return self._recurrence.find_recurrence(text)
