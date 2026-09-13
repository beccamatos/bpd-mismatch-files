from src.source import read_xlsx
from src.validation import validate_path
from src.index import FileIndex
from src.matcher import match
from src.report import write_report

# ------------------------------------------------------------------ settings
SHEET = "mismatched_text/file_paths.xlsx"   # <-- path to your .xlsx
ROOT = "mismatched_text"                     # <-- folder to scan for the real files
OUT = "match_report.xlsx"                # <-- where to write the report
SHEET_NAME = "File Paths"                # <-- worksheet name, or None for first
COLUMN = "File Path"                      # <-- header of the path column
# ---------------------------------------------------------------------------


def main():
    # 1. read the expected paths from the sheet
    raw_paths = read_xlsx(SHEET, sheet=SHEET_NAME, column=COLUMN)

    # 2. validate each one; keep the clean, set aside the rejected
    clean, rejected = [], []
    for raw in raw_paths:
        value, reason = validate_path(raw)
        if reason is None:
            clean.append(value)
        else:
            rejected.append((raw, reason))

    # 3. scan the disk once, then match every path against it
    index = FileIndex.scan(ROOT)
    results = [match(p, index) for p in clean]

    # 4. write the full colour-coded report
    tally = write_report(results, OUT)

    # 5. print a short summary so you can see what happened
    print(f"Checked {len(results)} rows -> {OUT}")
    for level in ("EXACT", "SAFE", "LOOSE", "NONE"):
        if tally.get(level):
            print(f"  {level:6} {tally[level]}")
    if rejected:
        print(f"  INVALID input rows: {len(rejected)}")
        for raw, reason in rejected:
            print(f"    {raw!r}: {reason}")


if __name__ == "__main__":
    main()