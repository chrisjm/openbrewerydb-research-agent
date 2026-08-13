# Glossary

| Term | Meaning |
| --- | --- |
| OBDB Record | Current brewery record fetched from Open Brewery DB API. |
| State License Record | Normalized record from a CA/CO/TX licensing adapter. |
| Candidate Record | Proposed updated record assembled from research signals. |
| Evidence Ref | Provenance object with source URL, snippet, fetched timestamp, and source type. |
| Field Diff | Typed delta for one field with old value, new value, confidence, and evidence refs. |
| Confidence Score | Numeric trust score in the range 0.0–1.0 with signal breakdown. |
| Output Gate | Rule that allows copyable CSV only when confidence meets threshold. |
| Swarm-safe Cache | TTL disk cache reused across runs for bulk state data. |
