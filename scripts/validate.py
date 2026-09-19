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

        definition = data["properties"].get("operational_area_definition")
        if definition and definition.get("type") == "Circle":
            definition_center = definition.get("center_point", {})
            stored_center = data["properties"].get("center_point", {})
            if stored_center and (
                abs(stored_center.get("latitude", 999) - definition_center.get("latitude", 999)) > 1e-5
                or abs(stored_center.get("longitude", 999) - definition_center.get("longitude", 999)) > 1e-5
            ):
                errors.append(f"{path}: center_point does not match operational_area_definition")
            radius = definition.get("radius_meters")
            if not isinstance(radius, (int, float)) or isinstance(radius, bool) or radius <= 0:
                errors.append(f"{path}: circle radius_meters must be greater than 0")
            elif radius > 20000000:
                errors.append(f"{path}: circle radius_meters exceeds 20000000")

        def safe_id(value):
            value = "".join("-" if not (char.isalnum() or char in "._-") else char for char in value)
            while "--" in value:
                value = value.replace("--", "-")
            return value.strip("-")[:80]

        expected = path.stem
        actual = data["properties"]["site_id"]
        expected_site = safe_id(actual)
        if expected != expected_site:
            errors.append(f"{path}: filename/site_id mismatch ({expected} != {expected_site})")

        operator_dir = path.parent.name
        operator_id = data["properties"]["operator_id"]
        expected_operator = safe_id(operator_id)
        if operator_dir != expected_operator:
            errors.append(f"{path}: directory/operator_id mismatch ({operator_dir} != {expected_operator})")

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
