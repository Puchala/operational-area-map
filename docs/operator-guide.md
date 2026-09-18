# Operator Guide

## Current POC workflow

1. Open the repository.
2. Select **Issues**.
3. Select **New issue**.
4. Choose **Publish Operational Area**.
5. Enter:
   - Operator ID
   - Site / Area ID
   - Metro / Locality
   - GeoJSON Feature
   - Optional coordination contact
   - Optional time information
6. Submit the issue.
7. A maintainer reviews the request.
8. The GeoJSON is added under:

```text
operational-areas/<OPERATOR-ID>/<SITE-ID>.geojson
```

9. GitHub Actions validate the file.
10. The overlap check reports any geographic intersection.
11. Once merged, the shared map is rebuilt.

## Important

The current GitHub Issue Form is a POC interface. GitHub does not provide a native map-drawing control inside Issue Forms.

A later version can provide a map-based drawing interface while keeping GitHub as the source of truth and review system.
