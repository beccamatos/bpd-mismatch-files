"""Normalization. 

How loosely two paths are allowed to match?

  SAFE  - trim whitespace, unify slashes, lowercase.
          Folds case + trailing-space + extension-case (.TXT vs .txt) +
          folder-case differences. These never create false matches between
          genuinely different files, so a SAFE hit can be auto-trusted.

  LOOSE - SAFE, plus folding of look-alike characters (I | 1 -> l, O -> 0).
          This is what rescues 'group_l' vs 'group_1' and 'fiIe' vs 'file',
          but the same rule *can* merge two genuinely different names, so a
          LOOSE-only hit must be surfaced for human review, never trusted blindly.
"""
from __future__ import annotations

import enum
import unicodedata


class MatchLevel(enum.IntEnum):
    """How a candidate matched. Ordered from most to least trustworthy."""
    EXACT = 0      # byte-for-byte identical to the listed path
    SAFE = 1       # equal after trim / slash / case folding  -> auto-trust
    LOOSE = 2      # equal only after look-alike folding       -> needs review
    NONE = 3       # no match at all                           -> missing

    @property
    def is_match(self) -> bool:
        return self is not MatchLevel.NONE

    @property
    def trusted(self) -> bool:
        return self in (MatchLevel.EXACT, MatchLevel.SAFE)


# Characters that look alike in most fonts, mapped to a single canonical form.
# Applied to an already-lowercased string, so we only need lowercase keys.
_CONFUSABLE = str.maketrans({"i": "l", "1": "l", "|": "l", "!": "l", "o": "0"})


def safe_key(path: str) -> str:
    """Canonical key for the SAFE tier: trim, unify slashes, unicode-normalize,
    lowercase. Two paths with the same safe_key differ only in ways that are
    almost always incidental (whitespace, separators, case)."""
    s = unicodedata.normalize("NFC", str(path)).strip()
    s = s.replace("\\", "/")
    while "//" in s:                      # collapse doubled separators
        s = s.replace("//", "/")
    s = s.strip("/")                      # ignore leading/trailing separators
    return s.lower()


def loose_key(path: str) -> str:
    """Canonical key for the LOOSE tier: safe_key plus look-alike folding.
    A collision here between two *different* real files means the fold was too
    aggressive for that pair; callers must treat loose-only hits as ambiguous."""
    return safe_key(path).translate(_CONFUSABLE)


def has_trailing_ws(path: str) -> bool:
    """True if the raw value carries leading/trailing whitespace -- a real
    defect worth reporting even when the path otherwise resolves."""
    s = str(path)
    return s != s.strip()