#!/usr/bin/env python3
"""Regression tests for positive-area and component-level overlap semantics."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_map_data.py"


def feature(operator_id, site_id, geometry, definition=None):
    return {
        "type": "Feature",
        "properties": {
            "operator_id": operator_id,
            "site_id": site_id,
            "operational_area_definition": definition or {"type": "Polygon"},
        },
        "geometry": geometry,
    }


def polygon(x1, y1, x2, y2):
    return {
        "type": "Polygon",
        "coordinates": [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]],
    }


def multipolygon(parts):
    return {
        "type": "MultiPolygon",
        "coordinates": [part["coordinates"][0] for part in parts],
    }


def run_builder(features):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        scripts = root / "scripts"
        areas = root / "operational-areas" / "test"
        scripts.mkdir(parents=True)
        areas.mkdir(parents=True)
        shutil.copy2(BUILD_SCRIPT, scripts / "build_map_data.py")
        for index, item in enumerate(features, start=1):
            (areas / f"{index}.geojson").write_text(json.dumps(item) + "\n", encoding="utf-8")
        output = root / "map.json"
        subprocess.run(
            [sys.executable, str(scripts / "build_map_data.py"), "--output", str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(output.read_text(encoding="utf-8"))["features"]


def test_touching_rectangles_are_not_overlap():
    features = run_builder([
        feature("A", "left", polygon(0, 0, 1, 1)),
        feature("B", "right", polygon(1, 0, 2, 1)),
    ])
    assert all(not item["properties"]["potential_overlap"] for item in features)
    assert all(not item["properties"]["potential_overlap_components"] for item in (f["properties"] for f in features))


def test_only_overlapping_multipolygon_part_is_reported():
    features = run_builder([
        feature("A", "two-rectangles", multipolygon([polygon(0, 0, 1, 1), polygon(2, 0, 3, 1)])),
        feature("B", "overlap-second", polygon(2.5, 0, 3.5, 1)),
    ])
    a = next(item for item in features if item["properties"]["operator_id"] == "A")
    b = next(item for item in features if item["properties"]["operator_id"] == "B")
    assert a["properties"]["potential_overlap"] is True
    assert a["properties"]["potential_overlap_components"] == [{
        "component_type": "Polygon",
        "component_index": 2,
        "other_operator_id": "B",
        "other_site_id": "overlap-second",
        "other_component_type": "Polygon",
        "other_component_index": 1,
    }]
    assert b["properties"]["potential_overlap_components"][0]["other_component_index"] == 2


def test_containment_is_overlap():
    features = run_builder([
        feature("A", "large", polygon(0, 0, 4, 4)),
        feature("B", "inside", polygon(1, 1, 2, 2)),
    ])
    assert all(item["properties"]["potential_overlap"] for item in features)


def main():
    test_touching_rectangles_are_not_overlap()
    test_only_overlapping_multipolygon_part_is_reported()
    test_containment_is_overlap()
    print("Overlap semantic regression tests passed.")


if __name__ == "__main__":
    main()
