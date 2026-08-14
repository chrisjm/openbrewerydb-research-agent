import json as _json

import httpx

from obdb.agent.state import OBDBRecord, StepError
from obdb.ports.obdb_port import OBDBQuery

_BASE = "https://api.openbrewerydb.org/v1"
_TIMEOUT = 10.0


def _to_record(raw: dict) -> OBDBRecord | StepError:
    try:
        return OBDBRecord(
            id=raw["id"],
            name=raw["name"],
            brewery_type=raw.get("brewery_type"),
            address_1=raw.get("address_1") or raw.get("street"),
            city=raw.get("city"),
            state_province=raw.get("state_province") or raw.get("state"),
            postal_code=raw.get("postal_code"),
            country=raw.get("country"),
            website_url=raw.get("website_url"),
            phone=raw.get("phone"),
            longitude=str(raw["longitude"]) if raw.get("longitude") is not None else None,
            latitude=str(raw["latitude"]) if raw.get("latitude") is not None else None,
        )
    except KeyError as exc:
        return StepError(step_id="obdb_lookup", message=f"Malformed record missing field: {exc}")


class OBDBApiAdapter:
    """Structured OBDB lookup via /breweries with by_name + location filters."""

    def lookup_one(self, query: OBDBQuery) -> OBDBRecord | StepError | None:
        params: dict = {"by_name": query.name, "per_page": 10}
        if query.state:
            params["by_state"] = query.state.lower()
        if query.city:
            params["by_city"] = query.city
        if query.postal_code:
            params["by_postal"] = query.postal_code

        try:
            resp = httpx.get(f"{_BASE}/breweries", params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return StepError(
                step_id="obdb_lookup",
                message=f"HTTP {exc.response.status_code} from OBDB API",
                source=str(exc.request.url),
            )
        except httpx.RequestError as exc:
            return StepError(
                step_id="obdb_lookup",
                message=f"Request error: {exc}",
                source=str(exc.request.url) if exc.request else None,
            )

        try:
            results = resp.json()
        except _json.JSONDecodeError:
            return StepError(
                step_id="obdb_lookup",
                message="Invalid JSON response from OBDB API",
                source=str(resp.url),
            )

        if not isinstance(results, list):
            return StepError(
                step_id="obdb_lookup",
                message=f"Unexpected response shape from OBDB API: {type(results).__name__}",
                source=str(resp.url),
            )

        if not results:
            return None

        raw = results[0]
        if not isinstance(raw, dict):
            return None
        return _to_record(raw)
