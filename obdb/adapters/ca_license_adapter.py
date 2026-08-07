import json as _json
from pathlib import Path

from obdb.agent.state import StateLicenseRecord, StepError

_FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "ca_license_hit.json"
_SOURCE_URL = "https://www.abc.ca.gov/licensing/licensing-reports/"
_STEP_ID = "ca_license_lookup"

# ponytail: CA ABC website renders license data via JavaScript/AJAX with expiring nonces.
# Automated bulk fetch is blocked without browser automation.
# Deferred to a future story when headless browser support is added.
_BLOCKER_MSG = (
    "CA ABC license data requires JavaScript rendering and session nonces. "
    "Automated fetch blocked. See deferred-work.md."
)


def _to_record(r: dict) -> StateLicenseRecord:
    try:
        return StateLicenseRecord(
            id=r["id"],
            name=r["name"],
            license_status=r.get("license_status"),
            address=r.get("address"),
            city=r.get("city"),
            state_code=r["state_code"],
            source_url=r.get("source_url", _SOURCE_URL),
            fetched_at=r["fetched_at"],
        )
    except KeyError as exc:
        raise exc


class CALicenseAdapter:
    """CA ABC license adapter.

    Default: synthetic JSON fixture (real source is blocked — see module comment).
    Live: always returns StepError; CA ABC requires JavaScript session auth.
    """

    state_code = "CA"
    country_code = "US"

    def fetch_bulk(self, *, live: bool = False) -> list[StateLicenseRecord] | StepError:
        if live:
            return StepError(step_id=_STEP_ID, message=_BLOCKER_MSG, source=_SOURCE_URL)
        try:
            raw_list = _json.loads(_FIXTURE.read_text())
            return [_to_record(r) for r in raw_list]
        except Exception as exc:
            return StepError(step_id=_STEP_ID, message=str(exc), source=str(_FIXTURE))

    def lookup_one(self, name: str, city: str) -> list[StateLicenseRecord] | StepError:
        result = self.fetch_bulk()
        if isinstance(result, StepError):
            return result
        name_l, city_l = name.lower(), city.lower()
        return [r for r in result if name_l in r.name.lower() and city_l in (r.city or "").lower()]
