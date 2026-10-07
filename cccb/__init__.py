"""CCCb: measures how alike two pieces of text are, and nothing else.

Two measurements, both deterministic and dependency-free:

* duplicate: is the overlap between two texts too long and specific to be
  coincidence (``cccb.matching``)?
* recurrence: do two texts share enough significant vocabulary to be the same
  pattern seen again (``cccb.recurrence``)?

``TextMatcher`` bundles both behind the interface CCC plugs in. CCCb holds no
records, makes no decisions and knows nothing about CCC: what a match means is
CCC's call.
"""

from .matcher import TextMatcher
from .matching import (
    DUPLICATE_THRESHOLD,
    MINIMUM_MATCH_LENGTH,
    MatchResult,
    ShingleIndex,
    anti_probability_of_coincidental_match,
    best_match_against,
)
from .recurrence import (
    MINIMUM_SIGNATURE_SIZE,
    RECURRENCE_THRESHOLD,
    RecurrenceDetector,
    concept_set,
)

__all__ = [
    "DUPLICATE_THRESHOLD",
    "MINIMUM_MATCH_LENGTH",
    "MINIMUM_SIGNATURE_SIZE",
    "RECURRENCE_THRESHOLD",
    "MatchResult",
    "RecurrenceDetector",
    "ShingleIndex",
    "TextMatcher",
    "anti_probability_of_coincidental_match",
    "best_match_against",
    "concept_set",
]

__version__ = "0.1.0"
