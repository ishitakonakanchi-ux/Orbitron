#!/usr/bin/env python3
"""
notebook_modifications.py
The notebook in the repo is unmodified

python notebook_modifications.py Orbitron.ipynb runnable.ipynb
"""

import json
import sys

COLAB_MARKERS = (
    "google.colab",
    "drive.mount",
    "/content/drive",
    "files.download",
)

# names used but not assigned
SESSION_GLOBALS = [
    "# --- injected by notebook_modifications.py: Colab session state ---\n",
    "import joblib\n",
    "n_detail_times = len(detail_times)   # 144 at the current 10-min cadence\n",
    "n_filter_times = 48                  # what the Colab kernel held\n",
    'print(f"Session globals: n_detail_times={n_detail_times}, '
    'n_filter_times={n_filter_times}")\n',
]

# the cell that defines detail_times
ANCHOR = "all_positions_detail = np.zeros("


def is_colab_cell(source: str) -> bool:
    return any(m in source for m in COLAB_MARKERS)


def main(src_path: str, out_path: str) -> int:
    with open(src_path) as f:
        nb = json.load(f)

    cells = nb.get("cells", [])

    skipped = []
    for i, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip() or not is_colab_cell(source):
            continue

        hit = next(m for m in COLAB_MARKERS if m in source)
        skipped.append((i, hit))
        # kept the original as a comment
        # replaced the cell with a no-op
        commented = "".join(f"# {line}" if line.strip() else line
                            for line in source.splitlines(keepends=True))
        cell["source"] = [
            f"# --- skipped by notebook_modifications.py: Colab-only ({hit}) ---\n",
            commented.rstrip("\n") + "\n",
            f'print("Skipped Colab cell {i}")\n',
        ]
        cell["outputs"] = []
        cell["execution_count"] = None

    # find the anchor and insert the missing globals just after it
    anchor_at = next(
        (i for i, c in enumerate(cells)
         if c.get("cell_type") == "code" and ANCHOR in "".join(c.get("source", []))),
        None,
    )
    if anchor_at is None:
        print(f"ERROR: anchor not found: {ANCHOR}")
        return 1

    injected = {
        "cell_type": "code",
        "metadata": {},
        "source": SESSION_GLOBALS,
        "outputs": [],
        "execution_count": None,
    }
    if any("id" in c for c in cells):
        injected["id"] = "injected-session-globals"
    cells.insert(anchor_at + 1, injected)

    with open(out_path, "w") as f:
        json.dump(nb, f)

    total = sum(1 for c in cells if c.get("cell_type") == "code")
    print(f"{src_path} -> {out_path}")
    print(f"  code cells: {total}, skipped: {len(skipped)}")
    for i, hit in skipped:
        print(f"    cell {i}: {hit}")
    if not skipped:
        print("  (no
