"""Disk index.

Scan the disk and build lookups so every later question is an instant
dict hit. Two dicts: First for exact/safe match? and second for look-alike match?
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .normalise import safe_key, loose_key


@dataclass
class FileIndex:
    root: str
    # safe_key(realpath) -> real path. Case/whitespace/slash folding
    # never merges genuinely different files, so one value here is safe.
    safe: dict[str, str] = field(default_factory=dict)
    # loose_key(realpath) -> list of real paths. Look-alike folding can merge
    # different files, so this must hold every candidate, not just one.
    loose: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def scan(cls, root: str) -> "FileIndex":
        idx = cls(root=root)
        # os.walk does the single pass over the whole tree, however deep.
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                full = os.path.join(dirpath, name)
                # store paths relative to root so they compare against the
                # Excel's relative paths (folder_b/group_1/file.txt).
                rel = os.path.relpath(full, root).replace("\\", "/")

                # --- safe dict: last-writer-wins is fine (no false merges) ---
                idx.safe[safe_key(rel)] = rel

                # --- loose dict: append.
                #     both candidates are kept so the matcher can say
                #     "several files claim this, human choice."
                idx.loose.setdefault(loose_key(rel), []).append(rel)
        return idx

    def find_safe(self, path: str) -> str | None:
        """Return the real file whose safe form equals this path's, or None."""
        return self.safe.get(safe_key(path))

    def find_loose(self, path: str) -> list[str]:
        """Return all real files whose loose form equals this path's.
        Empty list = no look-alike; one = clean look-alike; two+ = ambiguous."""
        return self.loose.get(loose_key(path), [])

    def __len__(self) -> int:
        # number of real files indexed (every file added exactly one safe key)
        return len(self.safe)