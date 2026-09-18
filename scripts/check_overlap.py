#!/usr/bin/env python3
"""Detect potential geographic overlap between published operational areas."""

import json
import sys
from pathlib import Path
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
areas = []

for path in sorted((ROOT / "operational-areas").glob("*/*.geojson")):
    data = json.loads(path.read_text())
    areas.append((path, data, shape(data["geometry"])))

found = False

for i, (path_a, data_a, geom_a) in enumerate(areas):
    for path_b, data_b, geom_b in areas[i + 1:]:
        if geom_a.intersects(geom_b):
            found = True
            a = data_a["properties"]
            b = data_b["properties"]
            print(
                f"POTENTIAL OVERLAP: "
                f"{a['operator_id']}/{a['site_id']} <-> "
                f"{b['operator_id']}/{b['site_id']}"
            )

if not found:
    print("No potential geographic overlaps detected.")
