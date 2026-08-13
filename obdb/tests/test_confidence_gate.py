from obdb.agent.state import BreweryRunState, OBDBRecord, WebsiteSignal
from obdb.domain.scoring import DEFAULT_CONFIDENCE_THRESHOLD, compute_confidence, evaluate_gate


def test_confidence_is_deterministic_for_same_state():
    state = BreweryRunState(
        target_name="Auburn Ale House",
        target_location="Auburn, CA",
        obdb_record=OBDBRecord(
            id="brew-1",
            name="Auburn Ale House",
            city="Auburn",
            state_province="California",
            country="US",
            website_url="https://brew.example",
        ),
        website_signal=WebsiteSignal(
            signal="active",
            final_url="https://brew.example",
            status_code=200,
            source_url="https://brew.example",
        ),
        state_license_records=[],
    )

    first = compute_confidence(state)
    second = compute_confidence(state)

    assert first == second
    assert first["score"] >= 0.0
    assert first["score"] <= 1.0


def test_default_threshold_is_0_7():
    assert DEFAULT_CONFIDENCE_THRESHOLD == 0.7
    assert evaluate_gate(0.69)["gate"] == "fail"
    assert evaluate_gate(0.7)["gate"] == "pass"


def test_gate_uses_override_threshold():
    assert evaluate_gate(0.69, threshold=0.5)["gate"] == "pass"
    assert evaluate_gate(0.69, threshold=0.8)["gate"] == "fail"
