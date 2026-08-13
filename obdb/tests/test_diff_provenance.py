from obdb.agent.state import OBDBRecord
from obdb.domain.diff import build_diff


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

    result = build_diff(current, candidate)

    assert result == [
        {
            "field": "website_url",
            "old_value": "https://brew.example",
            "new_value": "https://brew.example/closed",
            "confidence": 0.9,
            "evidence_refs": ["website_check"],
        }
    ]


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
