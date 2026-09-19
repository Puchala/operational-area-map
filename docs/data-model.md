# Data Model

Each published operational area is represented by one GeoJSON `Feature`.

## Required properties

- `operator_id`
- `site_id`
- `metro_locality`

## Optional properties

- `center_point`
- `geographic_bounds`
- `operational_area_definition`
- `coordination_contact`
- `effective_from`
- `effective_to`

## Geometry

The POC accepts:

- `Polygon`
- `MultiPolygon`

For circular operational areas, `geometry` contains a GeoJSON polygon approximation and `operational_area_definition` preserves the circle as center point plus radius in meters.

Example:

```json
"operational_area_definition": {
  "type": "Circle",
  "center_point": {
    "latitude": 37.355,
    "longitude": -121.915
  },
  "radius_meters": 1000
}
```

The circle definition is the explicit representation of the circular area. The polygon approximation supports standard GeoJSON interoperability, map rendering, and geographic overlap analysis.

Coordinates use standard GeoJSON longitude/latitude ordering.

## Privacy principle

The schema deliberately uses a closed set of properties. This prevents contributors from accidentally adding detailed operational or commercially sensitive information to the published record.
