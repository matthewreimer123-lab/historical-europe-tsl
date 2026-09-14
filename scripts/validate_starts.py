#!/usr/bin/env python3
"""Validate provisional TSL anchors against the planning grid."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

WIDTH = 120
HEIGHT = 80
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "major-starts.csv"


def main() -> int:
    errors: list[str] = []
    primary_occupants: dict[tuple[int, int], list[str]] = defaultdict(list)

    with CSV_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    required = {
        "civilization_type",
        "primary_x",
        "primary_y",
        "alternate_x",
        "alternate_y",
        "priority",
        "region",
        "anchor",
    }
    if not rows:
        errors.append("TSL table is empty")
    elif set(rows[0]) != required:
        errors.append(f"unexpected CSV columns: {sorted(rows[0])}")

    seen_civs: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        civ = row["civilization_type"]
        if civ in seen_civs:
            errors.append(f"line {line_number}: duplicate civilization {civ}")
        seen_civs.add(civ)

        for label in ("primary", "alternate"):
            try:
                x = int(row[f"{label}_x"])
                y = int(row[f"{label}_y"])
            except ValueError:
                errors.append(f"line {line_number}: {label} coordinate is not an integer")
                continue
            if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
                errors.append(
                    f"line {line_number}: {label} ({x}, {y}) is outside {WIDTH}x{HEIGHT}"
                )

        primary_occupants[(int(row["primary_x"]), int(row["primary_y"]))].append(civ)

    intentional_collisions = {
        frozenset(("CIVILIZATION_BYZANTIUM", "CIVILIZATION_OTTOMAN"))
    }
    for coordinate, civilizations in primary_occupants.items():
        if len(civilizations) > 1 and frozenset(civilizations) not in intentional_collisions:
            errors.append(f"unapproved primary collision at {coordinate}: {civilizations}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Validated {len(rows)} civilization starts on a {WIDTH}x{HEIGHT} grid.")
    print("Approved shared primary: Byzantium/Ottomans at Constantinople.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
