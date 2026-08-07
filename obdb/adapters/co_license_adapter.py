import json as _json
from pathlib import Path

from obdb.agent.state import StateLicenseRecord, StepError

_FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "co_license_hit.json"


def _to_record(r: dict) -> StateLicenseRecord:
    try:
        return StateLicenseRecord(
            id=r["id"],
            name=r["name"],
            license_status=r.get("license_status"),
            address=r.get("address"),
            city=r.get("city"),
            state_code=r["state_code"],
            source_url=r["source_url"],
            fetched_at=r["fetched_at"],
        )
    except KeyError as exc:
        raise exc


class COLicenseAdapter:
    """CO SBG license adapter — v0.1 uses static fixture; live HTTP deferred."""

    state_code = "CO"
    country_code = "US"

    def fetch_bulk(self) -> list[StateLicenseRecord] | StepError:
        try:
            raw_list = _json.loads(_FIXTURE.read_text())
            return [_to_record(r) for r in raw_list]
        except Exception as exc:
            return StepError(step_id="co_license_lookup", message=str(exc), source=str(_FIXTURE))

    def lookup_one(self, name: str, city: str) -> list[StateLicenseRecord] | StepError:
        result = self.fetch_bulk()
        if isinstance(result, StepError):
            return result
        name_l, city_l = name.lower(), city.lower()
        return [r for r in result if name_l in r.name.lower() and city_l in (r.city or "").lower()]
