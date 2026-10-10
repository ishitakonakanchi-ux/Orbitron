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

def is_colab_cell(source: str) -> bool:
    return any(m in source for m in COLAB_MARKERS)

def main(src_path: str, out_path: str) -> int:
    with open(src_path) as f:
        nb = json.load(f)

    skipped = []
    for i, cell in enumerate(nb.get("cells", [])):
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

    with open(out_path, "w") as f:
        json.dump(nb, f)

    total = sum(1 for c in nb.get("cells", []) if c.get("cell_type") == "code")
    print(f"{src_path} -> {out_path}")
    print(f"  code cells: {total}, skipped: {len(skipped)}")
    for i, hit in skipped:
        print(f"    cell {i}: {hit}")
    if not skipped:
        print("  (no Colab-only cells found)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
