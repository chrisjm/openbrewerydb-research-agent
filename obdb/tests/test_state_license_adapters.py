"""Snapshot fixture tests for CA, CO, TX license adapters (Story 1.2)."""

import importlib

import pytest

from obdb.adapters.ca_license_adapter import CALicenseAdapter
from obdb.adapters.co_license_adapter import COLicenseAdapter
from obdb.adapters.tx_license_adapter import TXLicenseAdapter
from obdb.agent.state import StateLicenseRecord, StepError
from obdb.ports.state_license_port import StateLicensePort

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


# ---------------------------------------------------------------------------
# Happy-path: fetch_bulk returns StateLicenseRecord list
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adapter_cls", [CALicenseAdapter, COLicenseAdapter, TXLicenseAdapter])
def test_fetch_bulk_returns_records(adapter_cls):
    result = adapter_cls().fetch_bulk()
    assert isinstance(result, list)
    assert len(result) >= 1
    assert all(isinstance(r, StateLicenseRecord) for r in result)


# ---------------------------------------------------------------------------
# lookup_one: hit and miss
# ---------------------------------------------------------------------------


def test_ca_lookup_one_hit():
    result = CALicenseAdapter().lookup_one("Anchor Brewing", "San Francisco")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == "CA-12345"


def test_ca_lookup_one_miss():
    result = CALicenseAdapter().lookup_one("Nonexistent Brewery", "Nowhere")
    assert result == []


def test_co_lookup_one_hit():
    result = COLicenseAdapter().lookup_one("New Belgium", "Fort Collins")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_co_lookup_one_miss():
    result = COLicenseAdapter().lookup_one("Ghost Brewery", "Denver")
    assert result == []


def test_tx_lookup_one_hit():
    result = TXLicenseAdapter().lookup_one("Saint Arnold", "Houston")
    assert isinstance(result, list)
    assert len(result) == 1


def test_tx_lookup_one_miss():
    result = TXLicenseAdapter().lookup_one("Ghost Brewery", "Austin")
    assert result == []


# ---------------------------------------------------------------------------
# Error path: malformed fixture returns StepError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "adapter_mod_name, adapter_cls, fixture_attr",
    [
        ("obdb.adapters.ca_license_adapter", CALicenseAdapter, "_FIXTURE"),
        ("obdb.adapters.co_license_adapter", COLicenseAdapter, "_FIXTURE"),
        ("obdb.adapters.tx_license_adapter", TXLicenseAdapter, "_FIXTURE"),
    ],
)
def test_fetch_bulk_malformed_returns_step_error(
    adapter_mod_name, adapter_cls, fixture_attr, tmp_path, monkeypatch
):
    mod = importlib.import_module(adapter_mod_name)
    bad = tmp_path / "bad.json"
    bad.write_text('[{"no_id": true}]')
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
    monkeypatch.setattr(mod, fixture_attr, tmp_path / "nonexistent.json")
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
    monkeypatch.setattr(mod, fixture_attr, tmp_path / "nonexistent.json")
    result = adapter_cls().lookup_one("Any", "City")
    assert isinstance(result, StepError)
