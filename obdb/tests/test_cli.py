"""Tests for the obdb-run CLI entry point."""

import pytest

from obdb.adapters.ca_license_adapter import CALicenseAdapter
from obdb.adapters.co_license_adapter import COLicenseAdapter
from obdb.adapters.tx_license_adapter import TXLicenseAdapter
from obdb.agent.state import BreweryRunState, StepError, StepOutcome


def test_state_adapter_maps_known_codes():
    from obdb.cli import _LICENSE_ADAPTERS

    assert _LICENSE_ADAPTERS["CA"] is CALicenseAdapter
    assert _LICENSE_ADAPTERS["CO"] is COLicenseAdapter
    assert _LICENSE_ADAPTERS["TX"] is TXLicenseAdapter


def test_adapters_carry_full_state_name_for_obdb():
    assert CALicenseAdapter.state_name == "California"
    assert COLicenseAdapter.state_name == "Colorado"
    assert TXLicenseAdapter.state_name == "Texas"


def test_unsupported_state_exits():
    from obdb.cli import main

    with pytest.raises(SystemExit) as exc:
        main(["Brewery", "--state", "NY"])
    assert exc.value.code != 0
    msg = str(exc.value)
    # Message names the unsupported state and the supported set.
    assert "NY" in msg
    assert "CA" in msg and "CO" in msg and "TX" in msg


def _stub_state(*, error: StepError | None = None) -> BreweryRunState:
    return BreweryRunState(
        target_name="Lone Pint",
        target_state="Texas",
        obdb_record=None,
        error=error,
        step_outcomes=[
            StepOutcome(step_id="obdb_lookup", status="ok", detail="ok"),
        ],
        rendered_output="rendered Lone Pint in Texas",
    )


def test_main_runs_pipeline_and_prints_outcomes(monkeypatch, capsys):
    from obdb import cli
    from obdb.agent.orchestrator import BreweryRunOrchestrator

    captured = {}

    def fake_run(self, name, *, state=None, city=None, postal_code=None):
        captured["name"] = name
        captured["state"] = state
        captured["city"] = city
        captured["postal_code"] = postal_code
        return _stub_state()

    monkeypatch.setattr(BreweryRunOrchestrator, "run", fake_run)

    code = cli.main(["Lone Pint", "--state", "TX", "--city", "Austin"])

    out = capsys.readouterr().out
    assert code == 0
    assert captured["name"] == "Lone Pint"
    assert captured["state"] == "Texas"  # full name for OBDB by_state filter
    assert captured["city"] == "Austin"
    assert "rendered Lone Pint in Texas" in out
    assert "--- step outcomes ---" in out
    assert "obdb_lookup" in out


def test_main_returns_nonzero_on_error(monkeypatch, capsys):
    from obdb import cli
    from obdb.agent.orchestrator import BreweryRunOrchestrator

    err = StepError(step_id="obdb_lookup", message="boom", code="technical_blocked")

    def fake_run(self, name, *, state=None, city=None, postal_code=None):
        return _stub_state(error=err)

    monkeypatch.setattr(BreweryRunOrchestrator, "run", fake_run)

    code = cli.main(["Brewery", "--state", "CA"])
    capsys.readouterr()
    assert code == 1
