# filematch

Check a list of file paths in an Excel sheet against the files that actually
exist on disk, and produce a colour-coded report showing for every row
whether it matched, how confident the match is, and if something is off, *why*.

The disk is scanned once, and every path is then an
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

In addition to status of mismatch, the report also gives a cause for every non-exact row, e.g. `case difference`,
`trailing whitespace`, `look-alike character`, `ambiguous - multiple possible files`,
`folder is empty`, `folder does not exist`, `no matching file in folder`.

"LOOSE" is separate from "SAFE" because folding case is always safe, but folding
look-alike characters (a lowercase `l` vs a capital `I` vs a digit `1`, which are
pixel-identical in most fonts) can occasionally merge two genuinely different
files. Those matches are resolved but flagged for a human, and if a path could
match *several* real files the tool refuses to guess and lists all candidates.

---

## Project layout

```
bpd/                        
├── pyproject.toml          
├── conftest.py             
├── main.py                 
├── src/                    
│   ├── __init__.py         
│   ├── normalise.py        
│   ├── index.py            
│   ├── matcher.py          
│   ├── source.py          
│   ├── validation.py       
│   └── report.py           
└── tests/                  
    ├── test_normalise.py
    ├── test_index.py
    └── test_matcher.py
```

---

## Setup uv

[uv](https://docs.astral.sh/uv/) is a fast Python package and environment manager.
It gives the project its own isolated environment, so you never fight over
"which Python am I using?".

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

## Running it

Everything is run from the project root with `uv run`, which guarantees the
project's environment (with openpyxl + pydantic) is used.

### Option A — edit-and-run script (`main.py`)

Open `main.py` and set the three paths near the top:

```python
SHEET = "mismatched_text/file_paths.xlsx"   #  Excel sheet
ROOT  = "mismatched_text"        # folder to scan for the real files
OUT   = "match_report.xlsx"       # where to write the report
```

Then:

```bash
cd /path/to/bpd
uv run python main.py
```

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

