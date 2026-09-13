"""Unit tests for the matcher.

Each test builds a disk with tmp_path, indexes it, then asserts the
verdict (level), the resolved file, and the cause for one known situation.
Covers all four rungs AND each distinct cause branch.
"""

from src.index import FileIndex
from src.matcher import match
from src.normalise import MatchLevel


def _index_with(tmp_path):
    """A known little tree: one real file, plus an empty folder."""
    (tmp_path / "grp").mkdir()
    (tmp_path / "grp" / "file_01.txt").write_text("x")
    (tmp_path / "empty").mkdir()
    return FileIndex.scan(str(tmp_path))


# --- rung 1: EXACT --------------------------------------------------------

def test_exact_match(tmp_path):
    idx = _index_with(tmp_path)
    r = match("grp/file_01.txt", idx)
    assert r.level is MatchLevel.EXACT
    assert r.resolved == "grp/file_01.txt"
    assert r.cause == ""                     # no problem to explain


# --- rung 2: SAFE (two different causes) ----------------------------------

def test_safe_case_difference(tmp_path):
    idx = _index_with(tmp_path)
    r = match("grp/FILE_01.TXT", idx)        # only case differs
    assert r.level is MatchLevel.SAFE
    assert r.resolved == "grp/file_01.txt"
    assert r.cause == "case difference"


def test_safe_trailing_whitespace(tmp_path):
    idx = _index_with(tmp_path)
    r = match("grp/file_01.txt ", idx)       # trailing space
    assert r.level is MatchLevel.SAFE
    assert r.resolved == "grp/file_01.txt"
    assert "trailing whitespace" in r.cause
    assert r.needs_trim is True


# --- rung 3: LOOSE (clean look-alike, and ambiguous) ----------------------

def test_loose_single_lookalike(tmp_path):
    idx = _index_with(tmp_path)
    r = match("grp/fi1e_01.txt", idx)        # digit 1 instead of letter l
    assert r.level is MatchLevel.LOOSE
    assert r.resolved == "grp/file_01.txt"
    assert "look-alike" in r.cause


def test_loose_ambiguous_keeps_no_single_resolution(tmp_path):
    # two real files collide on the loose key -> ambiguous
    (tmp_path / "run_1.txt").write_text("a")   # digit one
    (tmp_path / "run_l.txt").write_text("b")   # letter l
    idx = FileIndex.scan(str(tmp_path))
    # ask about 'run_I.txt' (capital I): NOT a real file, so it skips EXACT,
    # but folds to the same loose key as BOTH real files -> ambiguous.
    r = match("run_I.txt", idx)
    assert r.level is MatchLevel.LOOSE
    assert r.resolved is None                 # refuses to guess
    assert sorted(r.candidates) == ["run_1.txt", "run_l.txt"]
    assert "ambiguous" in r.cause


# --- rung 4: NONE (three different causes) --------------------------------

def test_none_empty_folder(tmp_path):
    idx = _index_with(tmp_path)
    r = match("empty/file_01.txt", idx)       # folder exists but is empty
    assert r.level is MatchLevel.NONE
    assert r.resolved is None
    assert r.cause == "folder is empty"


def test_none_missing_folder(tmp_path):
    idx = _index_with(tmp_path)
    r = match("ghost/file_01.txt", idx)       # folder does not exist
    assert r.level is MatchLevel.NONE
    assert r.cause == "folder does not exist"


def test_none_missing_file_in_real_folder(tmp_path):
    idx = _index_with(tmp_path)
    r = match("grp/file_99.txt", idx)         # folder real, file absent
    assert r.level is MatchLevel.NONE
    assert r.cause == "no matching file in folder"