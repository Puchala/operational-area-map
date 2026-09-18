#!/usr/bin/env python3
"""Validate operational-area GeoJSON files."""

import json
import sys
from pathlib import Path

try:
    from jsonschema import validate
    from shapely.geometry import shape
except ImportError as exc:
    print(f"Missing dependency: {exc}")
    print("Install with: pip install jsonschema shapely")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schema/operational-area.schema.json").read_text())

errors = []

for path in sorted((ROOT / "operational-areas").glob("*/*.geojson")):
    try:
        data = json.loads(path.read_text())
        validate(instance=data, schema=SCHEMA)
        geom = shape(data["geometry"])
        if not geom.is_valid:
            errors.append(f"{path}: invalid geometry: {geom.is_valid}")
        if geom.is_empty:
            errors.append(f"{path}: geometry is empty")

        expected = path.stem
        actual = data["properties"]["site_id"]
        if expected != actual:
            errors.append(f"{path}: filename/site_id mismatch ({expected} != {actual})")

        operator_dir = path.parent.name
        operator_id = data["properties"]["operator_id"]
        if operator_dir != operator_id:
            errors.append(f"{path}: directory/operator_id mismatch ({operator_dir} != {operator_id})")

        print(f"PASS  {path}")
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        print(f"FAIL  {path}: {exc}")

if errors:
    print("\nValidation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("\nAll operational areas passed validation.")
