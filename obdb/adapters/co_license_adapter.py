import csv as _csv
import io as _io
from datetime import datetime, timezone
from pathlib import Path

import httpx

from obdb.agent.state import StateLicenseRecord, StepError

_FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "co_license_hit.csv"
_SOURCE_URL = (
    "https://data.colorado.gov/resource/ier5-5ms2.csv"
    "?$where=license_type%20LIKE%20'%25Manufacturer%20(brewery)%25'"
    "&$limit=200"
    "&$select=licensee_name,doing_business_as,license_number,license_type,"
    "expiration,street_address,city,state,zip"
)
_STEP_ID = "co_license_lookup"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(raw: bytes) -> list[StateLicenseRecord]:
    reader = _csv.DictReader(_io.StringIO(raw.decode("utf-8")))
    records = []
    for row in reader:
        records.append(
            StateLicenseRecord(
                id=row["license_number"],
                name=row.get("doing_business_as") or row["licensee_name"],
                license_status=row.get("license_type"),
                address=row.get("street_address") or None,
                city=row.get("city") or None,
                state_code=row.get("state") or "CO",
                source_url="https://data.colorado.gov/resource/ier5-5ms2",
                fetched_at=_now(),
            )
        )
    return records


class COLicenseAdapter:
    """CO SBG license adapter. Default: CSV fixture. Live: Socrata open data API."""

    state_code = "CO"
    country_code = "US"

    def fetch_bulk(self, *, live: bool = False) -> list[StateLicenseRecord] | StepError:
        if live:
            try:
                resp = httpx.get(_SOURCE_URL, timeout=15.0, follow_redirects=True)
                resp.raise_for_status()
                _FIXTURE.write_bytes(resp.content)
            except Exception as exc:
                return StepError(step_id=_STEP_ID, message=str(exc), source=_SOURCE_URL)
        try:
            return _parse(_FIXTURE.read_bytes())
        except Exception as exc:
            return StepError(step_id=_STEP_ID, message=str(exc), source=str(_FIXTURE))

    def lookup_one(self, name: str, city: str) -> list[StateLicenseRecord] | StepError:
        result = self.fetch_bulk()
        if isinstance(result, StepError):
            return result
        name_l, city_l = name.lower(), city.lower()
        return [r for r in result if name_l in r.name.lower() and city_l in (r.city or "").lower()]
