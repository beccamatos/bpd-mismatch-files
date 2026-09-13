"""Matcher.

    EXACT  - raw path is byte-for-byte a real file            (trust)
    SAFE   - equal after case/whitespace/slash folding        (trust)
    REVIEW - only matches after look-alike folding (or is     (human decides)
             ambiguous: several files could be the one)
    NONE   - nothing on disk resembles it                     (missing)

The matcher returns a MatchResult - the shared verdict object that both the
report and the loader read.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .normalise import MatchLevel, has_trailing_ws
from .index import FileIndex


@dataclass
class MatchResult:
    expected: str                       # the raw path from the sheet
    level: MatchLevel                   # EXACT / SAFE / LOOSE / NONE
    resolved: str | None = None         # the real file, when we're confident
    candidates: list[str] = field(default_factory=list)  # for ambiguous LOOSE
    needs_trim: bool = False            # raw value had stray whitespace
    cause: str = ""                     # human explanation of WHY (blank if EXACT)

    @property
    def ok_to_load(self) -> bool:
        # only auto-open matches we trust; REVIEW/NONE never load unattended
        return self.level.trusted and self.resolved is not None


def _safe_cause(raw: str, hit: str, trim: bool) -> str:
    """Why did a non-exact SAFE match happen? Report the meaningful diffs;
    a mere \\ vs / separator difference is ubiquitous and not worth noting
    unless it is genuinely the only thing that differs."""
    reasons = []
    if trim:
        reasons.append("trailing whitespace")
    r = str(raw).replace("\\", "/").strip()
    if r.lower() == hit.lower() and r != hit:
        reasons.append("case difference")
    if reasons:
        return "; ".join(reasons)
    # nothing meaningful left -> it was only separators (or NFC/slash collapse)
    return "separator or formatting difference"


def _none_cause(raw: str, root: str) -> str:
    """Why did nothing match? Distinguish the three kinds of 'missing'."""
    rel_dir = os.path.dirname(str(raw).replace("\\", "/").strip())
    folder = os.path.join(root, rel_dir)
    if not os.path.isdir(folder):
        return "folder does not exist"
    if not any(os.scandir(folder)):
        return "folder is empty"
    return "no matching file in folder"


def match(expected: str, index: FileIndex) -> MatchResult:
    trim = has_trailing_ws(expected)

    # --- rungs 1 & 2: the safe dict answers -> EXACT or SAFE ---
    hit = index.find_safe(expected)
    if hit is not None:
        raw = str(expected).replace("\\", "/")
        if raw == hit:
            return MatchResult(expected, MatchLevel.EXACT, resolved=hit,
                               needs_trim=trim, cause="")
        return MatchResult(expected, MatchLevel.SAFE, resolved=hit,
                           needs_trim=trim,
                           cause=_safe_cause(expected, hit, trim))

    # --- rung 3: no safe hit, but a look-alike exists -> LOOSE ---
    cands = index.find_loose(expected)
    if cands:
        if len(cands) == 1:
            return MatchResult(expected, MatchLevel.LOOSE, resolved=cands[0],
                               candidates=list(cands), needs_trim=trim,
                               cause="look-alike character (e.g. l / I / 1 / O)")
        return MatchResult(expected, MatchLevel.LOOSE, resolved=None,
                           candidates=list(cands), needs_trim=trim,
                           cause="ambiguous - multiple possible files")

    # --- rung 4: nothing resembles it ---
    return MatchResult(expected, MatchLevel.NONE, needs_trim=trim,
                       cause=_none_cause(expected, index.root))