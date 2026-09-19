# Operator Guide

## Current POC workflow

1. Open the shared map or submission tool.
2. In the submission tool, choose one of the supported drawing options:
   - Polygon
   - Rectangle
   - Circle
3. For a polygon or rectangle, draw the operational area directly.
4. For a circle, click and drag from the center point to define the radius.
5. Review the shape, center point, geographic bounds, and radius when applicable.
6. Complete:
   - Operator ID
   - Site / Area ID
   - Metro / Locality
   - Optional coordination contact
   - Optional effective dates
7. For a circle, the center point and radius are preserved as the operational-area definition. A GeoJSON polygon approximation is generated for interoperability and overlap analysis.
8. Submit the request through the GitHub submission workflow.
9. GitHub Actions process and validate the submission.
10. The validated operational area is published to the shared map.

Published records are stored under:

```text
operational-areas/<OPERATOR-ID>/<SITE-ID>.geojson
```

## Geometry handling

The POC accepts:

- `Polygon`
- `MultiPolygon`

For circular operational areas, the published GeoJSON `geometry` is a polygon approximation, while `properties.operational_area_definition` preserves the circle definition:

```json
{
  "type": "Circle",
  "center_point": {
    "latitude": 37.355,
    "longitude": -121.915
  },
  "radius_meters": 1000
}
```

This allows the map and overlap analysis to use standard GeoJSON while retaining the original center-point-and-radius representation.

## Important

The submission tool is the preferred operator interface. Operators do not need to hand-author GeoJSON.

The map indicates potential geographic overlap for awareness. It does not determine whether coordination is required or authorize an operation.
