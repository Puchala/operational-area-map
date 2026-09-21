#!/usr/bin/env python3
"""Aggregate individual operational-area GeoJSON files into a FeatureCollection."""

import argparse
import copy
import json
import math
from pathlib import Path

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
AREA_EPSILON = 1e-12

parser = argparse.ArgumentParser()
parser.add_argument("--output", default=str(ROOT / "map/operational-areas.geojson"))
args = parser.parse_args()


def circle_to_polygon(center_lat, center_lng, radius_meters, segments=64):
    earth_radius = 6371008.8
    angular_distance = radius_meters / earth_radius
    lat1 = math.radians(center_lat)
    lon1 = math.radians(center_lng)
    coordinates = []
    for i in range(segments + 1):
        bearing = 2 * math.pi * i / segments
        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance)
            + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
        )
        coordinates.append([
            round((math.degrees(lon2) + 540) % 360 - 180, 7),
            round(math.degrees(lat2), 7),
        ])
    return {"type": "Polygon", "coordinates": [coordinates]}


def definition_circle_geometries(definition):
    geometries = []
    for circle in definition.get("circles") or []:
        center = circle.get("center_point") if isinstance(circle, dict) else None
        radius = circle.get("radius_meters") if isinstance(circle, dict) else None
        if not isinstance(center, dict) or not isinstance(radius, (int, float)):
            continue
        if not isinstance(center.get("latitude"), (int, float)) or not isinstance(center.get("longitude"), (int, float)):
            continue
        geometries.append(shape(circle_to_polygon(
            float(center["latitude"]),
            float(center["longitude"]),
            float(radius),
        )))
    return geometries


def canonical_geometry(data):
    """Build published geometry from the authoritative operational-area definition."""
    definition = data.get("properties", {}).get("operational_area_definition") or {}
    definition_type = definition.get("type")

    if definition_type == "MultiCircle":
        circles = definition_circle_geometries(definition)
        if not circles:
            return shape(data["geometry"])
        return unary_union(circles)

    if definition_type == "Circle":
        circles = definition_circle_geometries({"circles": [definition]})
        if circles:
            return circles[0]

    return shape(data["geometry"])


def polygon_components(data, geom):
    definition = data.get("properties", {}).get("operational_area_definition") or {}
    definition_type = definition.get("type")

    if definition_type == "MultiCircle":
        components = []
        for index, circle in enumerate(definition.get("circles") or [], start=1):
            center = circle.get("center_point") if isinstance(circle, dict) else None
            radius = circle.get("radius_meters") if isinstance(circle, dict) else None
            if not isinstance(center, dict) or not isinstance(radius, (int, float)):
                continue
            circle_geom = shape(circle_to_polygon(float(center["latitude"]), float(center["longitude"]), float(radius)))
            components.append(("Circle", index, circle_geom))
        return components

    if definition_type == "Circle":
        center = definition.get("center_point")
        radius = definition.get("radius_meters")
        if isinstance(center, dict) and isinstance(radius, (int, float)):
            circle_geom = shape(circle_to_polygon(float(center["latitude"]), float(center["longitude"]), float(radius)))
            return [("Circle", 1, circle_geom)]

    if isinstance(geom, Polygon):
        return [("Polygon", 1, geom)]
    if isinstance(geom, MultiPolygon):
        return [("Polygon", index, part) for index, part in enumerate(geom.geoms, start=1)]
    if isinstance(geom, GeometryCollection):
        components = []
        for part in geom.geoms:
            if isinstance(part, Polygon):
                components.append(("Polygon", len(components) + 1, part))
            elif isinstance(part, MultiPolygon):
                components.extend(("Polygon", len(components) + 1, child) for child in part.geoms)
        return components
    return []


items = []
for path in sorted((ROOT / "operational-areas").glob("*/*.geojson")):
    data = json.loads(path.read_text())
    items.append((path, data, canonical_geometry(data)))

features = []

for i, (path, data, geom) in enumerate(items):
    feature = copy.deepcopy(data)
    feature["geometry"] = mapping(geom)
    props = feature.setdefault("properties", {})
    overlaps = []
    overlap_details = []
    components = polygon_components(data, geom)

    for j, (other_path, other_data, other_geom) in enumerate(items):
        if i == j:
            continue

        intersection = geom.intersection(other_geom)
        if not intersection.is_empty and intersection.area > AREA_EPSILON:
            other_props = other_data["properties"]
            overlaps.append(f"{other_props['operator_id']}/{other_props['site_id']}")

        other_components = polygon_components(other_data, other_geom)
        for component_kind, component_index, component_geom in components:
            for other_kind, other_index, other_component_geom in other_components:
                component_intersection = component_geom.intersection(other_component_geom)
                if component_intersection.is_empty or component_intersection.area <= AREA_EPSILON:
                    continue
                other_props = other_data["properties"]
                overlap_details.append({
                    "component_type": component_kind,
                    "component_index": component_index,
                    "other_operator_id": other_props["operator_id"],
                    "other_site_id": other_props["site_id"],
                    "other_component_type": other_kind,
                    "other_component_index": other_index,
                })

    props["potential_overlap"] = bool(overlaps)
    props["potential_overlap_with"] = sorted(set(overlaps))
    props["potential_overlap_components"] = sorted(
        overlap_details,
        key=lambda item: (
            item["component_type"],
            item["component_index"],
            item["other_operator_id"],
            item["other_site_id"],
            item["other_component_type"],
            item["other_component_index"],
        ),
    )
    features.append(feature)

output = {
    "type": "FeatureCollection",
    "name": "operational-areas",
    "metadata": {
        "schema_version": "0.1",
        "purpose": "operational area overlap awareness",
        "note": "Potential overlap is informational and does not determine whether coordination is required.",
        "overlap_semantics": "Positive-area intersection; boundary-only touching is not classified as overlap.",
    },
    "features": features,
}

out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(output, indent=2) + "\n")
print(f"Wrote {len(features)} operational areas to {out}")