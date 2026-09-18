# Operational Area Map

A GitHub-native proof of concept for publishing **minimum necessary UAS operational-area information** so operators can identify potential geographic overlap and determine when operational-practicality coordination may be needed.

> **Status:** Technical Committee Proof of Concept  
> **Format:** GeoJSON  
> **Repository model:** GitHub + Pull Requests + GitHub Actions  
> **Scope:** Awareness and information sharing — not operational approval or coordination authority

---

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
Technical / Repository Review
   │
   ▼
Merge
   │
   ▼
Shared Operational Area Map
```

The repository keeps each operator's area in a separate GeoJSON file. GitHub Actions validates the submission and builds the shared map data.

---

## Published Operational Areas

| Operator | Site | Metro / Locality | Area | Potential Overlap |
|---|---|---|---|---|
| `OPERATOR-001` | `SITE-001` | Philadelphia | Area A | 🟠 Yes |
| `OPERATOR-002` | `SITE-002` | Philadelphia | Area B | 🟠 Yes |

The examples are fictional and exist only to demonstrate the workflow.

### 🗺️ View the shared map

After enabling GitHub Pages, the interactive map will be available from:

`https://<OWNER>.github.io/<REPOSITORY>/`

---

## Minimum information

The POC intentionally limits the published information to what is useful for overlap awareness.

| Field | Required | Purpose |
|---|---:|---|
| Operator ID | Yes | Identifies the operator |
| Site / Area ID | Yes | Identifies the published area |
| Metro / Locality | Yes | Provides human-readable geographic context |
| Operational Area Geometry | Yes | Shows the geographic area |
| Center Point | Optional | Useful for quick geographic reference |
| Geographic Bounds | Optional | Useful for simple discovery/filtering |
| Coordination Contact | Optional | Allows operators to initiate coordination |
| Time Information | Optional | Can be added if the committee determines it is needed |

## 🔒 Information intentionally not published

This mechanism is **not intended** to publish:

- Detailed flight plans
- Flight routes or trajectories
- Customer information
- Flight volumes
- Detailed operational strategies
- Other commercially sensitive operational information

The objective is to share the **minimum information necessary for awareness of potential geographic overlap**.

---

## Repository structure

```text
operational-area-map/
│
├── operational-areas/
│   ├── OPERATOR-001/
│   │   └── SITE-001.geojson
│   └── OPERATOR-002/
│       └── SITE-002.geojson
│
├── schema/
│   └── operational-area.schema.json
│
├── map/
│   └── operational-areas.geojson
│
├── scripts/
│   ├── validate.py
│   └── check_overlap.py
│
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   └── operator-guide.md
│
└── .github/
    ├── ISSUE_TEMPLATE/
    │   └── publish-operational-area.yml
    └── workflows/
        ├── validate.yml
        ├── overlap-check.yml
        └── build-map.yml
```

---

## How publication works

### 1. Operator prepares an operational area

The operator provides a GeoJSON `Feature` containing the minimum required metadata and polygon geometry.

### 2. Operator submits a GitHub request

The repository provides a **Publish Operational Area** Issue Form.

### 3. Validation runs

GitHub Actions checks:

- GeoJSON structure
- Required fields
- Geometry type
- Geometry validity
- Allowed metadata
- Operator/site naming conventions

### 4. Potential overlap is checked

The automation compares published geometries and identifies geographic intersections.

**Important:** an intersection is reported as **potential geographic overlap**. It does not mean that coordination is automatically required.

### 5. Repository review

A maintainer reviews the proposed change and merges the pull request when appropriate.

### 6. Shared map is updated

The published GeoJSON files are aggregated into the shared map dataset.

---

## Quick test

The repository contains two fictional areas that overlap.

You can test the POC by:

1. Creating a branch.
2. Editing `operational-areas/OPERATOR-001/SITE-001.geojson`.
3. Changing its polygon.
4. Opening a pull request.
5. Watching the validation workflow run.
6. Reviewing the overlap result.
7. Merging the change.
8. Opening the GitHub Pages map.

---

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
The repository README and map provide a simple way to understand published areas.

### Non-authoritative awareness
The map indicates potential geographic overlap. It does not determine whether a particular operation may proceed or whether coordination is required.

---

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

Those items can be addressed after the committee agrees on the basic mechanism and minimum information set.
