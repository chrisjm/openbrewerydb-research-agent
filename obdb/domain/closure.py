from __future__ import annotations

from obdb.agent.state import OBDBRecord


def is_closed_brewery(record: OBDBRecord | None) -> bool:
    if record is None:
        return False
    return (record.brewery_type or "").strip().lower() == "closed"
