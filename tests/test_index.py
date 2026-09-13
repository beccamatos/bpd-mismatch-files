"""Unit tests for the index module.

The index reads the disk, so each test first builds its own folder of
files with pytest's `tmp_path` fixture (a fresh temp dir, auto-deleted after),
then scans it. No dependence on any real data folder.
"""

from src.index import FileIndex


def _make_tree(root):
    """Create a small known set of files under `root` and return it.
    root is a pathlib.Path (that is what tmp_path gives us)."""
    (root / "group_1").mkdir()
    (root / "group_1" / "file_01.txt").write_text("hi")
    (root / "group_1" / "file_02.txt").write_text("hi")
    (root / "empty").mkdir()                       # a folder with no files
    return root


# --- scanning -------------------------------------------------------------

def test_scan_counts_only_files(tmp_path):
    _make_tree(tmp_path)
    idx = FileIndex.scan(str(tmp_path))
    # two real files; the empty folder contributes nothing
    assert len(idx) == 2


# --- exact / safe lookups -------------------------------------------------

def test_find_safe_hits_exact_path(tmp_path):
    _make_tree(tmp_path)
    idx = FileIndex.scan(str(tmp_path))
    assert idx.find_safe("group_1/file_01.txt") == "group_1/file_01.txt"


def test_find_safe_ignores_case(tmp_path):
    _make_tree(tmp_path)
    idx = FileIndex.scan(str(tmp_path))
    # asking with a different case still finds the real file
    assert idx.find_safe("GROUP_1/FILE_01.TXT") == "group_1/file_01.txt"


def test_find_safe_returns_none_when_absent(tmp_path):
    _make_tree(tmp_path)
    idx = FileIndex.scan(str(tmp_path))
    assert idx.find_safe("group_1/file_99.txt") is None


# --- loose (look-alike) lookups ------------------------------------------

def test_find_loose_matches_lookalike(tmp_path):
    _make_tree(tmp_path)
    idx = FileIndex.scan(str(tmp_path))
    # 'fi1e_01' (digit one) should fold to the real 'file_01'
    assert idx.find_loose("group_1/fi1e_01.txt") == ["group_1/file_01.txt"]


def test_find_loose_empty_when_nothing_resembles(tmp_path):
    _make_tree(tmp_path)
    idx = FileIndex.scan(str(tmp_path))
    assert idx.find_loose("group_1/zzzzz.txt") == []


# ---  ambiguity rule ------------------------------

def test_loose_keeps_all_candidates_on_collision(tmp_path):
    # two different real files that fold to the same loose key
    (tmp_path / "run_1.txt").write_text("one")   # digit one
    (tmp_path / "run_l.txt").write_text("ell")   # letter l
    idx = FileIndex.scan(str(tmp_path))
    hits = idx.find_loose("run_1.txt")
    # the index must keep BOTH, not silently pick one
    assert sorted(hits) == ["run_1.txt", "run_l.txt"]