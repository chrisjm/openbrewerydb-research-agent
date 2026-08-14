"""Direct tests for TextRenderer.render() with real BreweryRunState objects."""

from obdb.adapters.text_renderer import TextRenderer
from obdb.agent.state import (
    BreweryRunState,
    OBDBRecord,
    StateLicenseRecord,
    StepError,
    WebsiteAddress,
    WebsiteSignal,
)


def _record(**overrides) -> OBDBRecord:
    defaults = dict(
        id="brew-1",
        name="Lone Pint Brewery",
        brewery_type="micro",
        address_1="507 Commerce St",
        city="Magnolia",
        state_province="Texas",
        postal_code="77355",
        country="US",
        website_url="http://www.lonepint.com",
        phone="2817315466",
    )
    defaults.update(overrides)
    return OBDBRecord(**defaults)


def _license(**overrides) -> StateLicenseRecord:
    defaults = dict(
        id="TX-123",
        name="LONE PINT BREWERY LLC",
        license_status="Active",
        city="Magnolia",
        state_code="TX",
        source_url="https://data.texas.gov/resource/7hf9-qc9f",
        fetched_at="2026-08-13T00:00:00Z",
    )
    defaults.update(overrides)
    return StateLicenseRecord(**defaults)


def test_renders_header_with_target_name_and_location():
    out = TextRenderer().render(BreweryRunState(target_name="Lone Pint", target_state="Texas"))
    assert out.startswith("=== Lone Pint — Texas ===")


def test_renders_obdb_record_section_when_present():
    out = TextRenderer().render(
        BreweryRunState(target_name="Lone Pint", target_state="Texas", obdb_record=_record())
    )
    assert "OBDB Record" in out
    assert "brew-1" in out
    assert "Lone Pint Brewery" in out
    assert "micro" in out
    assert "507 Commerce St, Magnolia, Texas 77355" in out
    assert "http://www.lonepint.com" in out
    assert "2817315466" in out


def test_omits_obdb_record_section_when_absent():
    out = TextRenderer().render(BreweryRunState(target_name="Lone Pint", target_state="Texas"))
    assert "OBDB Record" not in out


def test_renders_state_license_records():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            state_license_records=[_license()],
        )
    )
    assert "State License Records" in out
    assert "[TX] LONE PINT BREWERY LLC — Magnolia — status: Active" in out


def test_omits_license_section_when_empty():
    out = TextRenderer().render(BreweryRunState(target_name="Lone Pint", target_state="Texas"))
    assert "State License Records" not in out


def test_renders_website_signal_active_with_url():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            website_signal=WebsiteSignal(
                signal="active",
                final_url="https://www.lonepint.com/",
                status_code=200,
                source_url="http://www.lonepint.com",
            ),
        )
    )
    assert "Website Signal" in out
    assert "signal:  active" in out
    assert "https://www.lonepint.com/  (HTTP 200)" in out


def test_renders_website_signal_unknown_without_url():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            website_signal=WebsiteSignal(
                signal="unknown",
                final_url="",
                status_code=0,
                source_url="",
            ),
        )
    )
    assert "signal:  unknown" in out
    # unknown signals omit the url line
    assert "(HTTP" not in out


def test_renders_website_signal_with_jsonld_address():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            website_signal=WebsiteSignal(
                signal="active",
                final_url="https://www.lonepint.com/",
                status_code=200,
                source_url="http://www.lonepint.com",
                extracted_address=WebsiteAddress(
                    street="507 Commerce St",
                    city="Magnolia",
                    state="TX",
                    postal_code="77355",
                ),
            ),
        )
    )
    assert "JSON-LD: 507 Commerce St, Magnolia, TX 77355" in out


def test_renders_confidence_and_gate():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            confidence={"score": 1.0, "threshold": 0.7},
            gate={"gate": "pass"},
        )
    )
    assert "Confidence: 1.0 / 0.7  →  gate: pass" in out


def test_renders_confidence_with_unknown_gate_when_missing():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            confidence={"score": 0.4, "threshold": 0.7},
        )
    )
    assert "gate: ?" in out


def test_renders_proposed_diffs():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            diff={
                "diff": [
                    {
                        "field": "address_1",
                        "old_value": "507 Commerce St",
                        "new_value": "507 COMMERCE ST",
                        "evidence_refs": ["state_license"],
                    }
                ]
            },
        )
    )
    assert "Proposed Diffs" in out
    assert "address_1" in out
    assert "507 Commerce St" in out
    assert "507 COMMERCE ST" in out
    assert "[state_license]" in out


def test_renders_error_when_present():
    out = TextRenderer().render(
        BreweryRunState(
            target_name="Lone Pint",
            target_state="Texas",
            error=StepError(step_id="obdb_lookup", message="HTTP 302 from OBDB API"),
        )
    )
    assert "⚠ Error [obdb_lookup]: HTTP 302 from OBDB API" in out


def test_minimal_state_renders_only_header():
    out = TextRenderer().render(BreweryRunState(target_name="Ghost Brewery"))
    # No location fields → target_location is empty, but the " — " separator stays.
    assert out.strip() == "=== Ghost Brewery —  ==="
