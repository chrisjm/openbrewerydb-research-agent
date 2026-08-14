import csv as _csv
import io as _io
from datetime import datetime, timezone
from pathlib import Path

import httpx

from obdb.agent.state import StateLicenseRecord, StepError
from obdb.ports.state_license_port import LicenseQuery

_FIXTURE = Path(__file__).parent.parent / "tests" / "fixtures" / "tx_license_hit.csv"
_SOURCE_URL = (
    "https://data.texas.gov/resource/7hf9-qc9f.csv"
    "?$where=license_type='BW'%20AND%20primary_status='Active'"
    "&$limit=200"
    "&$select=license_id,license_type,trade_name,owner,city,address,"
    "address_2,zip,state,county,license_status,expiration_date"
)
_STEP_ID = "tx_license_lookup"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(raw: bytes) -> list[StateLicenseRecord]:
    reader = _csv.DictReader(_io.StringIO(raw.decode("utf-8")))
    records = []
    for row in reader:
        raw_id = row.get("license_id", "")
        # Socrata returns numeric ids with trailing ".0" — strip it
        record_id = raw_id.rstrip(".0").rstrip(".") if raw_id.endswith(".0") else raw_id
        records.append(
            StateLicenseRecord(
                id=record_id,
                name=row["trade_name"],
                license_status=row.get("license_status") or None,
                address=row.get("address") or None,
                city=row.get("city") or None,
                state_code=row.get("state") or "TX",
                source_url="https://data.texas.gov/resource/7hf9-qc9f",
                fetched_at=_now(),
            )
        )
    return records


class TXLicenseAdapter:
    """TX TABC license adapter. Default: CSV fixture. Live: Socrata open data API."""

    state_code = "TX"
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

    def lookup_one(self, query: "LicenseQuery") -> list[StateLicenseRecord] | StepError:
        result = self.fetch_bulk()
        if isinstance(result, StepError):
            return result
        name_l = query.name.lower()
        matches = [r for r in result if name_l in r.name.lower()]
        if query.city:
            city_l = query.city.lower()
            matches = [r for r in matches if city_l in (r.city or "").lower()]
        return matches
