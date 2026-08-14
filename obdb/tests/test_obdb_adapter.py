"""Tests for OBDBApiAdapter — snapshot fixtures, no live HTTP."""

import json
from pathlib import Path

import pytest

from obdb.adapters.obdb_api_adapter import OBDBApiAdapter
from obdb.ports.obdb_port import OBDBQuery

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def hit_payload():
    return json.loads((FIXTURES / "obdb_search_hit.json").read_text())


@pytest.fixture()
def empty_payload():
    return json.loads((FIXTURES / "obdb_search_empty.json").read_text())


# ---------------------------------------------------------------------------
# AC-1: happy path — known brewery returns a populated OBDBRecord
# ---------------------------------------------------------------------------


def test_lookup_one_returns_obdb_record(httpx_mock, hit_payload):
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries?by_name=Second+Hand+Brewery&per_page=10&by_state=california&by_city=San+Francisco",
        json=hit_payload,
    )

    result = OBDBApiAdapter().lookup_one(
        OBDBQuery(name="Second Hand Brewery", city="San Francisco", state="California")
    )

    assert result is not None
    assert result.id == "secondhand-brewery-san-francisco-ca"
    assert result.name == "Second Hand Brewery"
    assert result.city == "San Francisco"
    assert result.state_province == "California"
    # frozen model — no mutation
    with pytest.raises(Exception):
        result.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC-2: not-found — empty response returns None
# ---------------------------------------------------------------------------


def test_lookup_one_returns_none_when_not_found(httpx_mock, empty_payload):
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries?by_name=Ghost+Brewery&per_page=10&by_state=colorado",
        json=empty_payload,
    )

    result = OBDBApiAdapter().lookup_one(OBDBQuery(name="Ghost Brewery", state="Colorado"))

    assert result is None


# ---------------------------------------------------------------------------
# Error path: 5xx → StepError, no unhandled exception
# ---------------------------------------------------------------------------


def test_lookup_one_surfaces_step_error_on_5xx(httpx_mock):
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries?by_name=Any+Brewery&per_page=10&by_state=texas",
        status_code=503,
    )
    from obdb.agent.state import StepError

    result = OBDBApiAdapter().lookup_one(OBDBQuery(name="Any Brewery", state="Texas"))

    assert isinstance(result, StepError)
    assert result.step_id == "obdb_lookup"
    assert "503" in result.message


# ---------------------------------------------------------------------------
# Coercion: API returns numeric lat/lon floats → OBDBRecord stores strings
# ---------------------------------------------------------------------------


def test_lookup_one_coerces_float_lat_lon(httpx_mock):
    payload = [
        {
            "id": "jester-king-brewery-austin-tx",
            "name": "Jester King Brewery",
            "brewery_type": "micro",
            "address_1": "13187 Fitzhugh Rd",
            "city": "Austin",
            "state_province": "Texas",
            "postal_code": "78736",
            "country": "United States",
            "longitude": -98.0824692,  # float — as the live API actually returns
            "latitude": 30.2547264,
            "phone": "5125375100",
            "website_url": "http://www.jesterkingbrewery.com",
        }
    ]
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries?by_name=Jester+King&per_page=10&by_state=texas",
        json=payload,
    )

    result = OBDBApiAdapter().lookup_one(OBDBQuery(name="Jester King", state="Texas"))

    assert result is not None
    assert result.longitude == "-98.0824692"
    assert result.latitude == "30.2547264"


# ---------------------------------------------------------------------------
# OBDBQuery: construction fails without any location field
# ---------------------------------------------------------------------------


def test_obdb_query_requires_location():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="at least one location field"):
        OBDBQuery(name="Ghost Brewery")


# ---------------------------------------------------------------------------
# OBDBPort protocol compliance
# ---------------------------------------------------------------------------


def test_adapter_implements_obdb_port():
    from obdb.ports.obdb_port import OBDBPort

    assert isinstance(OBDBApiAdapter(), OBDBPort)
