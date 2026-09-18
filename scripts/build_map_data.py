#!/usr/bin/env python3
"""Aggregate individual operational-area GeoJSON files into a FeatureCollection."""

import argparse
import copy
import json
from pathlib import Path
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument("--output", default=str(ROOT / "map/operational-areas.geojson"))
args = parser.parse_args()

items = []
for path in sorted((ROOT / "operational-areas").glob("*/*.geojson")):
    data = json.loads(path.read_text())
    items.append((path, data, shape(data["geometry"])))

features = []

for i, (path, data, geom) in enumerate(items):
    feature = copy.deepcopy(data)
    props = feature.setdefault("properties", {})
    overlaps = []

    for j, (other_path, other_data, other_geom) in enumerate(items):
        if i == j:
            continue
        if geom.intersects(other_geom):
            other_props = other_data["properties"]
            overlaps.append(
                f"{other_props['operator_id']}/{other_props['site_id']}"
            )

    props["potential_overlap"] = bool(overlaps)
    props["potential_overlap_with"] = sorted(overlaps)
    features.append(feature)

output = {
    "type": "FeatureCollection",
    "name": "operational-areas",
    "metadata": {
        "schema_version": "0.1",
        "purpose": "operational area overlap awareness",
        "note": "Potential overlap is informational and does not determine whether coordination is required."
    },
    "features": features
}

out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(output, indent=2) + "\n")
print(f"Wrote {len(features)} operational areas to {out}")
