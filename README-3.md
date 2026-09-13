# filematch

Check a list of file paths in an Excel sheet against the files that actually
exist on disk, and produce a colour-coded report showing — for every row —
whether it matched, how confident the match is, and if something is off, *why*.

It is built to scale: the disk is scanned **once**, and every path is then an
instant lookup, so it works the same on 100 files or 100,000.

---

## What it does

Given an Excel sheet listing expected paths (e.g. `folder_b/group_1/file_01.txt`)
and a folder of real files, it classifies each row into one of four verdicts:

| Status | Meaning | Report colour |
|--------|---------|---------------|
| `EXACT` | byte-for-byte identical to a real file | green |
| `SAFE`  | matches after ignoring case / whitespace / slashes — trust it | amber |
| `LOOSE` | only matches after folding look-alike characters (`l`/`I`/`1`/`O`) — **review it** | orange |
| `NONE`  | nothing on disk corresponds to it — missing | red |

The report also gives a **cause** for every non-exact row, e.g. `case difference`,
`trailing whitespace`, `look-alike character`, `ambiguous - multiple possible files`,
`folder is empty`, `folder does not exist`, `no matching file in folder`.

Why "LOOSE" is separate from "SAFE": folding case is always safe, but folding
look-alike characters (a lowercase `l` vs a capital `I` vs a digit `1`, which are
pixel-identical in most fonts) can occasionally merge two genuinely different
files. Those matches are resolved but flagged for a human, and if a path could
match *several* real files the tool refuses to guess and lists all candidates.

---

## Project layout

```
bpd/                        <- project root (run everything from here)
├── pyproject.toml          <- created by uv; lists dependencies
├── conftest.py             <- empty file; lets pytest find the `src` package
├── main.py                 <- entry point you run (edit paths at the top)
├── src/                    <- the package (building blocks)
│   ├── __init__.py         <- marks `src` as a package (can be empty)
│   ├── normalise.py        <- matching rules: safe_key / loose_key / MatchLevel
│   ├── index.py            <- scans the disk once into fast lookup dictionaries
│   ├── matcher.py          <- the verdict ladder: EXACT / SAFE / LOOSE / NONE + cause
│   ├── source.py           <- reads expected paths from the .xlsx
│   ├── validation.py       <- pydantic checks on input paths (blank/absolute/escape)
│   └── report.py           <- writes the colour-coded .xlsx report
└── tests/                  <- unit tests (run with pytest)
    ├── test_normalise.py
    ├── test_index.py
    └── test_matcher.py
```

**The golden rule about imports and running files:**

- Files **inside** `src/` import each other with a leading dot: `from .index import FileIndex`.
  You **never run these directly** — they are building blocks, only imported.
- Files **outside** `src/` (like `main.py`) import with the full name, no dot:
  `from src.index import FileIndex`. These are the **only** files you run.

---

## Getting started (cloning this repo)

[uv](https://docs.astral.sh/uv/) is a fast Python package and environment manager.
It gives the project its own isolated environment, so you never fight over
"which Python am I using?". Everything the project needs is already recorded in
`pyproject.toml`, so setup is two commands.

### 1. Install uv (if you don't have it)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then close and reopen your terminal so `uv` is on your PATH. Check it:

```bash
uv --version
```

### 2. Sync the environment

From the project root, this reads `pyproject.toml` and installs **everything**
(openpyxl, pydantic, and the pytest dev tool) into a local `.venv`:

```bash
cd /path/to/bpd
uv sync
```

That's it — the project is ready. There is nothing else to install.

### 3. Confirm it worked

```bash
uv run pytest -q
```

You should see `24 passed`.

---

<details>
<summary>Maintainer note — how the dependencies got recorded (you do NOT need this to run the project)</summary>

The dependencies in `pyproject.toml` were originally added with `uv add`, which
installs a package **and** writes it into `pyproject.toml` so it is reproducible.
You only run these when *adding a new* dependency, never when cloning:

```bash
uv add openpyxl        # read/write Excel files
uv add pydantic        # input validation
uv add --dev pytest    # test runner (dev-only)
```

After any `uv add`, commit the updated `pyproject.toml` and `uv.lock` so the next
person who clones gets the same versions from a plain `uv sync`.

</details>

---

## Running it

Everything is run from the project root with `uv run`, which guarantees the
project's environment (with openpyxl + pydantic) is used.

### Option A — edit-and-run script (`main.py`)

Open `main.py` and set the three paths near the top:

```python
SHEET = "data/file_paths.xlsx"   # your Excel sheet
ROOT  = "data"                    # folder to scan for the real files
OUT   = "match_report.xlsx"       # where to write the report
```

Then:

```bash
cd /path/to/bpd
uv run python main.py
```

It prints a summary and writes the report:

```
Checked 100 rows -> match_report.xlsx
  EXACT  85
  SAFE   2
  LOOSE  3
  NONE   10
```

### Option B — interactive one-offs

Poke at any building block through the package (note: from the root, using
`src.`):

```bash
uv run python -c "from src.validation import validate_path; print(validate_path('/etc/passwd'))"
# -> (None, "absolute path not allowed: '/etc/passwd'")
```

`validate_path` returns `(clean_value, reason)`. `reason is None` means valid;
a reason string means rejected.

---

## Running the tests

From the project root:

```bash
uv run pytest            # run everything
uv run pytest -v         # verbose: list each test by name
uv run pytest tests/test_matcher.py            # one file
uv run pytest tests/test_matcher.py::test_exact_match   # one test
```

Expected: `24 passed`. A dot is a passing test; an `F` is a failure and names
exactly which behaviour broke.

If you see `ModuleNotFoundError: No module named 'src'` when running tests, make
sure the empty `conftest.py` exists in the project root — it tells pytest where
the `src` package lives.

---

## The report columns

| Column | Contents |
|--------|----------|
| `File Path` | the path exactly as written in the Excel sheet |
| `disk_path` | the real file it resolved to (blank if missing / ambiguous) |
| `status` | `EXACT` / `SAFE` / `LOOSE` / `NONE` |
| `cause` | why it is not an exact match (blank for `EXACT`) |

The original sheet is never modified — a fresh report file is always written.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `attempted relative import with no known parent package` | you ran a file *inside* `src/` directly | run `main.py` instead, or import via `uv run python -c "from src...."` |
| `No module named 'src'` (running a script) | not running from the project root | `cd` to `bpd/` first |
| `No module named 'src'` (running pytest) | pytest can't find the package root | add an empty `conftest.py` in `bpd/` |
| `No module named 'openpyxl'` / `'pydantic'` | wrong environment | use `uv run python ...`, and `uv add` the package |
| `No module named 'normalise'` | filename/import spelling mismatch (`normalise` vs `normalize`) | make the import match the actual filename exactly |

---

## How it works (one paragraph)

`source.py` reads the expected paths from the sheet. `validation.py` rejects any
that are blank, non-string, absolute, or use `..` to escape the scanned folder.
`index.py` walks the disk **once** and files every real path into two dictionaries
— a `safe` one (keyed by case/whitespace-folded path) and a `loose` one (also
folding look-alikes, keyed to a *list* of files so collisions are never silently
dropped). `matcher.py` then, for each path, asks the index two questions and walks
a four-rung ladder (exact string match → safe-key hit → loose-key hit → nothing)
to produce a `MatchResult` carrying the status, the resolved file, and the cause.
`report.py` writes those results to a fresh, colour-coded Excel file. Decide once,
present many ways.
