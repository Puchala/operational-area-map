# Operational Area Map

A GitHub-native proof of concept for publishing **minimum necessary UAS operational-area information** so operators can identify potential geographic overlap and determine when operational-practicality coordination may be needed.

> **Status:** Technical Committee Proof of Concept  
> **Format:** GeoJSON  
> **Repository model:** GitHub + Pull Requests + GitHub Actions  
> **Scope:** Awareness and information sharing — not operational approval or coordination authority

## 🗺️ What this demonstrates

```text
Operator
   │
   ▼
Publish Operational Area
   │
   ▼
GitHub Pull Request
   │
   ├── GeoJSON validation
   ├── Required-field validation
   └── Potential-overlap check
   │
   ▼
Repository Review
   │
   ▼
Merge
   │
   ▼
Shared Operational Area Map
```

Each published area is stored as a separate GeoJSON file. GitHub Actions validates the data and builds the dataset used by the interactive GitHub Pages map.

## Published demo operational areas

The repository currently contains **four fictional demonstration areas** with mock contact information. The data is intentionally illustrative and does not represent real operators, operations, or contact details.

| Operator | Site / Area | Metro / Locality | Potential overlap |
|---|---|---|---|
| `DEMO-ALPHA` | `SJC-NORTH-01` | San Jose, CA | 🟠 With DEMO-BRAVO |
| `DEMO-BRAVO` | `SJC-SOUTH-01` | San Jose, CA | 🟠 With DEMO-ALPHA |
| `DEMO-CHARLIE` | `MTV-EAST-01` | Mountain View, CA | 🔵 None detected |
| `DEMO-DELTA` | `AUS-NORTH-01` | Austin, TX | 🔵 None detected |

The two San Jose demonstration areas intentionally overlap so the automated overlap visualization can be exercised. The Mountain View and Austin areas provide non-overlapping examples.

### 🗺️ View the shared map

The interactive map is published through GitHub Pages from the repository's `main` branch. It displays the published areas, potential-overlap status, effective dates, and the mock coordination contact information.

## Minimum information

The POC intentionally limits the published information to what is useful for overlap awareness.

| Field | Required | Purpose |
|---|---:|---|
| Operator ID | Yes | Identifies the publishing operator |
| Site / Area ID | Yes | Identifies the published area |
| Metro / Locality | Yes | Provides human-readable geographic context |
| Operational Area Geometry | Yes | Shows the geographic area |
| Center Point | Optional | Useful for quick geographic reference |
| Geographic Bounds | Optional | Useful for discovery/filtering |
| Coordination Contact | Optional | Allows operators to initiate follow-up |
| Time Information | Optional | Indicates the effective period when provided |

## 🔒 Information intentionally not published

This mechanism is **not intended** to publish:

- Detailed flight plans
- Flight routes or trajectories
- Customer information
- Flight volumes
- Detailed operational strategies
- Other commercially sensitive operational information

The objective is to share the **minimum information necessary for awareness of potential geographic overlap**.

## Repository structure

```text
operational-area-map/
│
├── operational-areas/
│   ├── DEMO-ALPHA/
│   │   └── SJC-NORTH-01.geojson
│   ├── DEMO-BRAVO/
│   │   └── SJC-SOUTH-01.geojson
│   ├── DEMO-CHARLIE/
│   │   └── MTV-EAST-01.geojson
│   └── DEMO-DELTA/
│       └── AUS-NORTH-01.geojson
│
├── schema/
│   └── operational-area.schema.json
│
├── scripts/
│   ├── validate.py
│   ├── check_overlap.py
│   └── build_map_data.py
│
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   └── operator-guide.md
│
├── index.html
└── .github/
    └── workflows/
        ├── validate.yml
        └── build-map.yml
```

## How publication works

### 1. Operator prepares an operational area

The operator provides a GeoJSON `Feature` containing the minimum required metadata and polygon geometry.

### 2. Operator submits a change

The operational-area file is proposed through the repository's normal Git workflow and pull-request review process.

### 3. Validation runs

GitHub Actions checks the operational-area files against the schema and validates geometry-related requirements.

### 4. Potential overlap is checked

The map-build process compares published geometries and identifies geographic intersections.

**Important:** an intersection is reported as **potential geographic overlap**. It does not mean that coordination is automatically required.

### 5. Repository review

A maintainer reviews the proposed change and merges the pull request when appropriate.

### 6. Shared map is updated

GitHub Actions aggregates the operational-area files into the GeoJSON dataset used by the GitHub Pages map.

## Design principles

### Minimum necessary information
Publish enough information to support awareness without exposing unnecessary business or operational detail.

### Operator-controlled
Operators are responsible for the information they publish.

### Git-native
Changes are version-controlled, reviewable, auditable, and reversible.

### Machine-readable
GeoJSON provides a standard geographic interchange format.

### Human-readable
The README and interactive map provide a simple way to understand published areas and initiate follow-up using the published contact information.

### Non-authoritative awareness
The map indicates potential geographic overlap. It does not determine whether a particular operation may proceed or whether coordination is required.

## POC scope

This repository is intended to demonstrate the proposed mechanism to the Technical Committee.

It is **not** intended to define:

- final governance
- final publication policy
- final schema
- authorization to operate
- operational approval
- coordination procedures
- security/privacy requirements for a production system
