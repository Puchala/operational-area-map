# Data Model

Each published operational area is represented by one GeoJSON `Feature`.

## Required properties

- `operator_id`
- `site_id`
- `metro_locality`

## Optional properties

- `center_point`
- `geographic_bounds`
- `coordination_contact`
- `effective_from`
- `effective_to`

## Geometry

The POC accepts:

- `Polygon`
- `MultiPolygon`

Coordinates use standard GeoJSON longitude/latitude ordering.

## Privacy principle

The schema deliberately uses a closed set of properties. This prevents contributors from accidentally adding detailed operational or commercially sensitive information to the published record.
