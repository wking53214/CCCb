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

from typing import Optional

from . import matching
from .recurrence import RecurrenceDetector

__all__ = ["TextMatcher"]


class TextMatcher:
    """Duplicate and recurrence measurement over the texts it has been given."""

    def __init__(self) -> None:
        self._shingles = matching.ShingleIndex()
        self._recurrence = RecurrenceDetector()

    def add(self, item_id: str, text: str) -> None:
        self._shingles.add(item_id, text)
        self._recurrence.register(item_id, text)

    def duplicate_of(self, text: str) -> Optional[tuple[str, float, int]]:
        candidates = self._shingles.candidates_for(text)
        match = matching.best_match_against(text, candidates)
        if match is None or not match[1].implausible_as_coincidence:
            return None
        item_id, result = match
        return (item_id, result.anti_probability, result.match_length)

    def recurrence_of(
        self, text: str
    ) -> Optional[tuple[str, float, tuple[tuple[str, float], ...]]]:
        return self._recurrence.find_recurrence(text)
