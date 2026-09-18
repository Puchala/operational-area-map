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
Operational Area Drawing Tool
   │
   ▼
Submission Form
   │
   ▼
Automatic Draft Pull Request
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

The repository now supports an operator-friendly submission path: an operator draws an area in the browser, submits the minimum metadata through a GitHub Issue Form, and GitHub Actions converts the submission into a draft Pull Request. Publication still requires validation and human review.

## Operator submission flow

### 1. Draw the area

Open the **Operational Area Drawing Tool** on the GitHub Pages site. Draw a polygon or rectangle, review it, and copy the generated GeoJSON geometry.

The tool also calculates the center point and geographic bounds for convenience.

### 2. Submit the minimum information

Open the **Submit Operational Area** Issue Form and provide:

- Operator ID
- Site / Area ID
- Metro / Locality
- Generated Polygon / MultiPolygon geometry
- Optional center point and geographic bounds
- Optional coordination contact
- Optional effective dates

The form explicitly confirms that sensitive operational information should not be submitted.

### 3. Automatic PR creation

When the form is submitted, GitHub Actions:

1. Parses the structured issue-form fields.
2. Validates the submitted geometry type and JSON structure.
3. Creates an isolated submission branch.
4. Creates or updates the operator/site GeoJSON file.
5. Opens a **draft Pull Request** with a standardized review checklist.
6. Links the PR back to the originating submission issue.
7. Closes the processed submission issue.

### 4. Automated validation

The normal Pull Request validation workflow runs against the generated file. The map-build workflow performs the potential-overlap analysis after publication to `main`.

### 5. Human review and publication

A maintainer reviews the geometry, minimum-information boundary, metadata, contact information, dates, and automated checks. The area is not published merely because the submission form was completed.

After merge, GitHub Actions rebuilds the shared GeoJSON dataset and republishes the GitHub Pages map.

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
├── submit.html
└── .github/
    ├── ISSUE_TEMPLATE/
    │   └── operational-area.yml
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        ├── process-operational-area-submission.yml
        ├── validate.yml
        └── build-map.yml
```

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
The README, drawing tool, submission form, and interactive map provide a simple operator experience without requiring operators to hand-author GeoJSON.

### Safe-by-default publication
The submission workflow produces a draft PR. Automated processing does not itself publish an operational area.

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
