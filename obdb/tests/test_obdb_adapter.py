"""Tests for OBDBApiAdapter — snapshot fixtures, no live HTTP."""

import json
from pathlib import Path

import pytest

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
        url="https://api.openbrewerydb.org/v1/breweries/search?query=Second+Hand+Brewery&per_page=5",
        json=hit_payload,
    )
    from obdb.adapters.obdb_api_adapter import OBDBApiAdapter

    adapter = OBDBApiAdapter()
    result = adapter.lookup_one("Second Hand Brewery", "San Francisco, CA")

    assert result is not None
    assert result.id == "secondhand-brewery-san-francisco-ca"
    assert result.name == "Second Hand Brewery"
    assert result.city == "San Francisco"
    assert result.state_province == "California"
    # frozen model — no mutation
    with pytest.raises(Exception):
        result.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# AC-2: not-found — empty response returns None (no crash)
# ---------------------------------------------------------------------------


def test_lookup_one_returns_none_when_not_found(httpx_mock, empty_payload):
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries/search?query=Ghost+Brewery&per_page=5",
        json=empty_payload,
    )
    from obdb.adapters.obdb_api_adapter import OBDBApiAdapter

    adapter = OBDBApiAdapter()
    result = adapter.lookup_one("Ghost Brewery", "Denver, CO")

    assert result is None


# ---------------------------------------------------------------------------
# AC-2: filter mismatch — city/state doesn't match, returns None
# ---------------------------------------------------------------------------


def test_lookup_one_returns_none_when_location_mismatch(httpx_mock, hit_payload):
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries/search?query=Second+Hand+Brewery&per_page=5",
        json=hit_payload,
    )
    from obdb.adapters.obdb_api_adapter import OBDBApiAdapter

    adapter = OBDBApiAdapter()
    result = adapter.lookup_one("Second Hand Brewery", "Denver, CO")

    assert result is None


# ---------------------------------------------------------------------------
# Error path: 5xx → StepError, no unhandled exception
# ---------------------------------------------------------------------------


def test_lookup_one_surfaces_step_error_on_5xx(httpx_mock):
    httpx_mock.add_response(
        url="https://api.openbrewerydb.org/v1/breweries/search?query=Any+Brewery&per_page=5",
        status_code=503,
    )
    from obdb.adapters.obdb_api_adapter import OBDBApiAdapter
    from obdb.agent.state import StepError

    adapter = OBDBApiAdapter()
    result = adapter.lookup_one("Any Brewery", "Austin, TX")

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
        url="https://api.openbrewerydb.org/v1/breweries/search?query=Jester+King&per_page=5",
        json=payload,
    )
    from obdb.adapters.obdb_api_adapter import OBDBApiAdapter

    result = OBDBApiAdapter().lookup_one("Jester King", "Texas")

    assert result is not None
    assert result.longitude == "-98.0824692"
    assert result.latitude == "30.2547264"


# ---------------------------------------------------------------------------
# OBDBPort protocol compliance
# ---------------------------------------------------------------------------


def test_adapter_implements_obdb_port():
    from obdb.adapters.obdb_api_adapter import OBDBApiAdapter
    from obdb.ports.obdb_port import OBDBPort

    adapter = OBDBApiAdapter()
    # Runtime isinstance check via Protocol (runtime_checkable)
    assert isinstance(adapter, OBDBPort)
