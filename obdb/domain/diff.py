from __future__ import annotations

from obdb.agent.state import OBDBRecord


def build_diff(current: OBDBRecord, candidate: OBDBRecord) -> list[dict]:
    changes: list[dict] = []
    fields = OBDBRecord.model_fields
    for field_name in sorted(
        {
            key
            for key in fields
            if key in fields and getattr(current, key) != getattr(candidate, key)
        }
    ):
        if field_name in {"id", "name"}:
            continue
        changes.append(
            {
                "field": field_name,
                "old_value": getattr(current, field_name),
                "new_value": getattr(candidate, field_name),
                "confidence": 0.9,
                "evidence_refs": ["website_check"],
            }
        )
    return changes
