"""Snapshot fixture tests for CA, CO, TX license adapters (Story 1.2 / 1.2b)."""

import importlib

import pytest

from obdb.adapters.ca_license_adapter import CALicenseAdapter
from obdb.adapters.co_license_adapter import COLicenseAdapter
from obdb.adapters.tx_license_adapter import TXLicenseAdapter
from obdb.agent.state import StateLicenseRecord, StepError
from obdb.ports.state_license_port import LicenseQuery, StateLicensePort

# ---------------------------------------------------------------------------
# Protocol compliance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_cls", [CALicenseAdapter, COLicenseAdapter, TXLicenseAdapter])
def test_adapter_implements_port(adapter_cls):
    assert isinstance(adapter_cls(), StateLicensePort)


@pytest.mark.parametrize(
    "adapter_cls, expected_code",
    [(CALicenseAdapter, "CA"), (COLicenseAdapter, "CO"), (TXLicenseAdapter, "TX")],
)
def test_adapter_state_code(adapter_cls, expected_code):
    assert adapter_cls.state_code == expected_code


@pytest.mark.parametrize("adapter_cls", [CALicenseAdapter, COLicenseAdapter, TXLicenseAdapter])
def test_adapter_country_code_defaults_us(adapter_cls):
    assert adapter_cls.country_code == "US"


# ---------------------------------------------------------------------------
# Happy-path: fetch_bulk returns StateLicenseRecord list (offline/default)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_cls", [CALicenseAdapter, COLicenseAdapter, TXLicenseAdapter])
def test_fetch_bulk_returns_records(adapter_cls):
    result = adapter_cls().fetch_bulk()
    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(r, StateLicenseRecord) for r in result)


# ---------------------------------------------------------------------------
# lookup_one: hit and miss using fixture data
# ---------------------------------------------------------------------------


def test_ca_lookup_one_hit():
    result = CALicenseAdapter().lookup_one(
        LicenseQuery(name="Anchor Brewing", city="San Francisco")
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == "CA-12345"


def test_ca_lookup_one_miss():
    result = CALicenseAdapter().lookup_one(LicenseQuery(name="Nonexistent Brewery", city="Nowhere"))
    assert result == []


def test_co_lookup_one_hit():
    # Real fixture contains Odell Brewing CO Inc in Fort Collins
    result = COLicenseAdapter().lookup_one(LicenseQuery(name="Odell Brewing", city="Fort Collins"))
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0].state_code == "CO"


def test_co_lookup_one_miss():
    result = COLicenseAdapter().lookup_one(LicenseQuery(name="Ghost Brewery", city="Denver"))
    assert result == []


def test_tx_lookup_one_hit():
    # Real fixture contains SAINT ARNOLD BREWING COMPANY in Houston
    result = TXLicenseAdapter().lookup_one(LicenseQuery(name="Saint Arnold", city="Houston"))
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].state_code == "TX"


def test_tx_lookup_one_miss():
    result = TXLicenseAdapter().lookup_one(LicenseQuery(name="Ghost Brewery", city="Amarillo"))
    assert result == []


# ---------------------------------------------------------------------------
# live=True: CA always returns StepError (source blocked)
# ---------------------------------------------------------------------------


def test_ca_live_fetch_returns_step_error():
    result = CALicenseAdapter().fetch_bulk(live=True)
    assert isinstance(result, StepError)
    assert result.step_id == "ca_license_lookup"
    assert result.message  # non-empty blocker message


# ---------------------------------------------------------------------------
# live=True: CO and TX fetch from URL, save fixture, return records (mocked)
# ---------------------------------------------------------------------------

_CO_CSV = (
    '"licensee_name","doing_business_as","license_number","license_type",'
    '"expiration","street_address","city","state","zip"\n'
    '"TEST BREWING LLC","TEST BREWING","99-99999","Manufacturer (brewery)",'
    '"2027-01-01T00:00:00.000","1 Test St","Boulder","CO","80301.0"\n'
)

_TX_CSV = (
    '"license_id","license_type","trade_name","owner","city","address","address_2",'
    '"zip","state","county","license_status","expiration_date"\n'
    '"999999.0","BW","TEST BREWERY TX","TEST OWNER","Austin","1 Test St",,'
    '"78701","TX","Travis","Active","2028-01-01T00:00:00.000"\n'
)


def test_co_live_fetch_saves_fixture_and_returns_records(httpx_mock, tmp_path, monkeypatch):
    import obdb.adapters.co_license_adapter as mod

    fake_fixture = tmp_path / "co_test.csv"
    monkeypatch.setattr(mod, "_FIXTURE", fake_fixture)
    httpx_mock.add_response(content=_CO_CSV.encode())

    result = COLicenseAdapter().fetch_bulk(live=True)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].state_code == "CO"
    assert result[0].id == "99-99999"
    assert fake_fixture.exists()


def test_tx_live_fetch_saves_fixture_and_returns_records(httpx_mock, tmp_path, monkeypatch):
    import obdb.adapters.tx_license_adapter as mod

    fake_fixture = tmp_path / "tx_test.csv"
    monkeypatch.setattr(mod, "_FIXTURE", fake_fixture)
    httpx_mock.add_response(content=_TX_CSV.encode())

    result = TXLicenseAdapter().fetch_bulk(live=True)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].state_code == "TX"
    assert fake_fixture.exists()


def test_co_live_fetch_http_error_returns_step_error(httpx_mock):
    httpx_mock.add_response(status_code=503)
    result = COLicenseAdapter().fetch_bulk(live=True)
    assert isinstance(result, StepError)
    assert result.step_id == "co_license_lookup"


def test_tx_live_fetch_http_error_returns_step_error(httpx_mock):
    httpx_mock.add_response(status_code=503)
    result = TXLicenseAdapter().fetch_bulk(live=True)
    assert isinstance(result, StepError)
    assert result.step_id == "tx_license_lookup"


# ---------------------------------------------------------------------------
# Error path: malformed/missing fixture returns StepError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "adapter_mod_name, adapter_cls, fixture_attr, bad_content",
    [
        ("obdb.adapters.ca_license_adapter", CALicenseAdapter, "_FIXTURE", b'[{"no_id": true}]'),
        (
            "obdb.adapters.co_license_adapter",
            COLicenseAdapter,
            "_FIXTURE",
            b"bad,csv\nno,headers\n",
        ),
        (
            "obdb.adapters.tx_license_adapter",
            TXLicenseAdapter,
            "_FIXTURE",
            b"bad,csv\nno,headers\n",
        ),
    ],
)
def test_fetch_bulk_malformed_returns_step_error(
    adapter_mod_name, adapter_cls, fixture_attr, bad_content, tmp_path, monkeypatch
):
    mod = importlib.import_module(adapter_mod_name)
    bad = tmp_path / "bad_fixture"
    bad.write_bytes(bad_content)
    monkeypatch.setattr(mod, fixture_attr, bad)
    result = adapter_cls().fetch_bulk()
    assert isinstance(result, StepError)


@pytest.mark.parametrize(
    "adapter_mod_name, adapter_cls, fixture_attr",
    [
        ("obdb.adapters.ca_license_adapter", CALicenseAdapter, "_FIXTURE"),
        ("obdb.adapters.co_license_adapter", COLicenseAdapter, "_FIXTURE"),
        ("obdb.adapters.tx_license_adapter", TXLicenseAdapter, "_FIXTURE"),
    ],
)
def test_fetch_bulk_missing_file_returns_step_error(
    adapter_mod_name, adapter_cls, fixture_attr, tmp_path, monkeypatch
):
    mod = importlib.import_module(adapter_mod_name)
    monkeypatch.setattr(mod, fixture_attr, tmp_path / "nonexistent")
    result = adapter_cls().fetch_bulk()
    assert isinstance(result, StepError)


@pytest.mark.parametrize(
    "adapter_mod_name, adapter_cls, fixture_attr",
    [
        ("obdb.adapters.ca_license_adapter", CALicenseAdapter, "_FIXTURE"),
        ("obdb.adapters.co_license_adapter", COLicenseAdapter, "_FIXTURE"),
        ("obdb.adapters.tx_license_adapter", TXLicenseAdapter, "_FIXTURE"),
    ],
)
def test_lookup_one_propagates_step_error(
    adapter_mod_name, adapter_cls, fixture_attr, tmp_path, monkeypatch
):
    mod = importlib.import_module(adapter_mod_name)
    monkeypatch.setattr(mod, fixture_attr, tmp_path / "nonexistent")
    result = adapter_cls().lookup_one(LicenseQuery(name="Any", city="City"))
    assert isinstance(result, StepError)
