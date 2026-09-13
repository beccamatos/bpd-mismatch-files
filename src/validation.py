"""
An "invalid" row is one we refuse to even try to match (garbled/empty/unsafe).
That is different from a "mismatch", which is a well-formed path that simply
didn't line up with a real file - that stays the matcher's job.
"""
from __future__ import annotations

from pydantic import BaseModel, field_validator, ConfigDict


class ExpectedPath(BaseModel):
    """A single, validated expected path from the sheet.

    If construction succeeds, `value` is a clean relative path safe to match.
    If it fails, pydantic raises ValidationError naming the exact rule broken.
    """
    model_config = ConfigDict(str_strip_whitespace=False)  # we inspect ws ourselves

    value: str

    @field_validator("value")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if v is None or str(v).strip() == "":
            raise ValueError("empty or blank path")
        return v

    @field_validator("value")
    @classmethod
    def _is_relative(cls, v: str) -> str:
        s = str(v).replace("\\", "/")
        # an absolute path (/foo or C:/foo) breaks the relative-to-root contract
        if s.startswith("/") or (len(s) > 1 and s[1] == ":"):
            raise ValueError(f"absolute path not allowed: {v!r}")
        return v

    @field_validator("value")
    @classmethod
    def _no_escape(cls, v: str) -> str:
        # '..' segments can escape the root we scanned - refuse them
        parts = str(v).replace("\\", "/").split("/")
        if ".." in parts:
            raise ValueError(f"path escapes root with '..': {v!r}")
        return v


class ValidationError(BaseModel):
    """A row that failed validation, kept so the report can show it."""
    raw: object
    reason: str


def validate_path(raw: object) -> tuple[str | None, str | None]:
    """Return (clean_value, None) if valid, else (None, reason).

    Never raises - a batch of 1000 rows must survive one bad row. We convert
    pydantic's exception into a plain reason string for the caller.
    """
    from pydantic import ValidationError as PydErr
    try:
        return ExpectedPath(value=raw).value, None
    except PydErr as e:
        # pull the human message out of pydantic's structured error
        reason = "; ".join(err["msg"].replace("Value error, ", "")
                           for err in e.errors())
        return None, reason