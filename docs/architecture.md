# Architecture

## POC architecture

```text
                 ┌─────────────────────┐
                 │       Operator      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   GitHub Issue Form │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Pull Request / PR  │
                 └──────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       GeoJSON validation          Overlap detection
              │                           │
              └─────────────┬─────────────┘
                            ▼
                 ┌─────────────────────┐
                 │  Repository Review  │
                 └──────────┬──────────┘
                            │
                         merge
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Shared GeoJSON    │
                 │       + Map         │
                 └─────────────────────┘
```

GitHub provides version control, review, audit history, and automation.

GeoJSON is the interchange format.

The map is a visualization of published data.
