from obdb.agent.state import (
    BreweryRunState,
    OBDBRecord,
    StateLicenseRecord,
    WebsiteAddress,
    WebsiteSignal,
)
from obdb.domain.diff import build_candidate, build_diff


def test_build_diff_returns_field_changes_with_provenance():
    current = OBDBRecord(
        id="brew-1",
        name="Auburn Ale House",
        city="Auburn",
        state_province="California",
        country="US",
        website_url="https://brew.example",
    )
    candidate = OBDBRecord(
        id="brew-1",
        name="Auburn Ale House",
        city="Auburn",
        state_province="California",
        country="US",
        website_url="https://brew.example/closed",
    )

    result = build_diff(current, candidate, sources={"website_url": "website_jsonld"})

    assert result == [
        {
            "field": "website_url",
            "old_value": "https://brew.example",
            "new_value": "https://brew.example/closed",
            "confidence": 0.9,
            "evidence_refs": ["website_jsonld"],
        }
    ]


def test_build_diff_uses_external_when_no_sources():
    current = OBDBRecord(id="b", name="X", address_1="Old St")
    candidate = OBDBRecord(id="b", name="X", address_1="New St")

    result = build_diff(current, candidate)
    assert result[0]["evidence_refs"] == ["external"]


def test_build_diff_returns_empty_list_for_no_change():
    record = OBDBRecord(
        id="brew-1",
        name="Auburn Ale House",
        city="Auburn",
        state_province="California",
        country="US",
        website_url="https://brew.example",
    )
    assert build_diff(record, record) == []


def test_build_candidate_prefers_website_jsonld_over_license():
    obdb = OBDBRecord(
        id="brew-1", name="Test", address_1="13187 Fitzhugh Rd", city="Austin", state_province="TX"
    )
    state = BreweryRunState(
        target_name="Test",
        target_state="TX",
        obdb_record=obdb,
        state_license_records=[
            StateLicenseRecord(
                id="123",
                name="TEST",
                address="13005 FITZHUGH RD",
                city="AUSTIN",
                state_code="TX",
                source_url="https://example.com",
                fetched_at="2026-01-01T00:00:00Z",
            )
        ],
        website_signal=WebsiteSignal(
            signal="active",
            final_url="https://test.com",
            status_code=200,
            source_url="https://test.com",
            extracted_address=WebsiteAddress(
                street="13187 Fitzhugh Rd", city="Austin", state="TX", postal_code="78736"
            ),
        ),
    )

    candidate, sources = build_candidate(state)

    assert candidate.address_1 == "13187 Fitzhugh Rd"
    assert sources["address_1"] == "website_jsonld"
    assert candidate.postal_code == "78736"
    assert sources["postal_code"] == "website_jsonld"


def test_build_candidate_falls_back_to_license_when_no_jsonld():
    obdb = OBDBRecord(id="brew-1", name="Test", address_1="Old Address", city="Austin")
    state = BreweryRunState(
        target_name="Test",
        target_state="TX",
        obdb_record=obdb,
        state_license_records=[
            StateLicenseRecord(
                id="123",
                name="TEST",
                address="13005 FITZHUGH RD",
                city="AUSTIN",
                state_code="TX",
                source_url="https://example.com",
                fetched_at="2026-01-01T00:00:00Z",
            )
        ],
    )

    candidate, sources = build_candidate(state)

    assert candidate.address_1 == "13005 FITZHUGH RD"
    assert sources["address_1"] == "state_license"
