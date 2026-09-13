"""Unit tests for the normalise module
"""

from src.normalise import safe_key, loose_key, has_trailing_ws


# --- safe_key: folds only INCIDENTAL differences -------------------------

def test_safe_key_folds_extension_case():
    # .TXT and .txt are the same file at the safe tier
    assert safe_key("file_05.TXT") == safe_key("file_05.txt")


def test_safe_key_folds_slash_direction():
    # backslash vs forward slash must not matter
    assert safe_key(r"folder\file.txt") == safe_key("folder/file.txt")


def test_safe_key_ignores_trailing_space():
    assert safe_key("file_04.txt ") == safe_key("file_04.txt")


def test_safe_key_does_not_fold_lookalikes():
    # this is LOOSE's job, NOT safe's - proving the tiers stay separate
    assert safe_key("group_l") != safe_key("group_1")


# --- loose_key: additionally folds LOOK-ALIKE characters -----------------

def test_loose_key_folds_l_and_one():
    # lowercase L vs digit one
    assert loose_key("group_l") == loose_key("group_1")


def test_loose_key_folds_capital_i_and_l():
    # capital I vs lowercase l (the invisible 'file' vs 'fiIe' bug)
    assert loose_key("fiIe_04.txt") == loose_key("file_04.txt")


def test_loose_key_keeps_real_differences_apart():
    # folding must NOT collapse genuinely different names
    assert loose_key("file_02.txt") != loose_key("file_03.txt")


# --- has_trailing_ws: the whitespace-defect detector ---------------------

def test_has_trailing_ws_true_for_trailing_space():
    assert has_trailing_ws("file_04.txt ") is True


def test_has_trailing_ws_false_for_clean_value():
    assert has_trailing_ws("file_04.txt") is False