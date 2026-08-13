from obdb.agent.state import OBDBRecord
from obdb.domain.closure import is_closed_brewery


def test_closed_brewery_type_is_detected():
    record = OBDBRecord(
        id="brew-1",
        name="Closed House",
        brewery_type="closed",
        city="Auburn",
        state_province="California",
        country="US",
    )

    assert is_closed_brewery(record) is True


def test_non_closed_brewery_type_is_not_detected():
    record = OBDBRecord(
        id="brew-2",
        name="Open House",
        brewery_type="micro",
        city="Auburn",
        state_province="California",
        country="US",
    )

    assert is_closed_brewery(record) is False


def test_missing_record_is_not_closed():
    assert is_closed_brewery(None) is False
