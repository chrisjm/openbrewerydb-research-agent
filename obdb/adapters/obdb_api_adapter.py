import httpx

from obdb.agent.state import OBDBRecord, StepError

_BASE = "https://api.openbrewerydb.org/v1"
_TIMEOUT = 10.0


def _location_matches(record: dict, location: str) -> bool:
    """Word-boundary check: any location token matches a word in city or state fields."""
    tokens = {t.strip().lower() for t in location.replace(",", " ").split() if t.strip()}
    city = (record.get("city") or "").lower()
    state = (record.get("state_province") or record.get("state") or "").lower()
    haystack_words = set((city + " " + state).split())
    return bool(tokens & haystack_words)


def _to_record(raw: dict) -> OBDBRecord:
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
        longitude=raw.get("longitude"),
        latitude=raw.get("latitude"),
    )


class OBDBApiAdapter:
    """Runtime OBDB lookup via the public API (AD-3: no bulk-cache path here)."""

    def lookup_one(self, name: str, location: str) -> OBDBRecord | StepError | None:
        params = {"query": name, "per_page": 5}
        try:
            resp = httpx.get(f"{_BASE}/breweries/search", params=params, timeout=_TIMEOUT)
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
                source=str(exc.request.url),
            )

        results = resp.json()
        for raw in results:
            if _location_matches(raw, location):
                return _to_record(raw)
        return None
