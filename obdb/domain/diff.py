from __future__ import annotations

from obdb.agent.state import BreweryRunState, OBDBRecord


def build_candidate(state: BreweryRunState) -> tuple[OBDBRecord, dict[str, str]]:
    """
    Build a candidate OBDBRecord from gathered evidence.
    Returns (candidate, field_sources) where field_sources maps field → evidence source.

    Priority: website JSON-LD > state license > OBDB current (unchanged).
    Only fields with evidence from an external source are overridden.
    """
    if state.obdb_record is None:
        raise ValueError("Cannot build candidate without an OBDB record")

    overrides: dict[str, object] = {}
    sources: dict[str, str] = {}

    # State license — lower priority; often a registered/mailing address
    for rec in state.state_license_records:
        if rec.address and "address_1" not in overrides:
            overrides["address_1"] = rec.address
            sources["address_1"] = "state_license"
        if rec.city and "city" not in overrides:
            overrides["city"] = rec.city
            sources["city"] = "state_license"

    # Website JSON-LD — higher priority; overrides license when present
    addr = (state.website_signal or None) and (state.website_signal.extracted_address or None)
    if addr is not None:
        _maybe("address_1", addr.street, "website_jsonld", overrides, sources)
        _maybe("city", addr.city, "website_jsonld", overrides, sources)
        _maybe("state_province", addr.state, "website_jsonld", overrides, sources)
        _maybe("postal_code", addr.postal_code, "website_jsonld", overrides, sources)
        _maybe("phone", addr.phone, "website_jsonld", overrides, sources)
        _maybe("latitude", addr.latitude, "website_jsonld", overrides, sources)
        _maybe("longitude", addr.longitude, "website_jsonld", overrides, sources)

    return state.obdb_record.model_copy(update=overrides), sources


def _maybe(
    field: str,
    value: object,
    source: str,
    overrides: dict,
    sources: dict,
) -> None:
    if value is not None:
        overrides[field] = value
        sources[field] = source


def build_diff(
    current: OBDBRecord,
    candidate: OBDBRecord,
    sources: dict[str, str] | None = None,
) -> list[dict]:
    changes: list[dict] = []
    fields = OBDBRecord.model_fields
    for field_name in sorted(
        key for key in fields if getattr(current, key) != getattr(candidate, key)
    ):
        if field_name in {"id", "name"}:
            continue
        evidence = [sources[field_name]] if sources and field_name in sources else ["external"]
        changes.append(
            {
                "field": field_name,
                "old_value": getattr(current, field_name),
                "new_value": getattr(candidate, field_name),
                "confidence": 0.9,
                "evidence_refs": evidence,
            }
        )
    return changes
