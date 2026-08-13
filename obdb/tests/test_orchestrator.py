from obdb.agent.orchestrator import BreweryRunOrchestrator
from obdb.agent.state import OBDBRecord, StepError, WebsiteSignal


class StubOBDBAdapter:
    def __init__(self):
        self.calls = []

    def lookup_one(self, name: str, location: str):
        self.calls.append(("obdb_lookup", name, location))
        return OBDBRecord(
            id="brew-1",
            name=name,
            city="Auburn",
            state_province="California",
            country="US",
            website_url="https://brew.example",
        )


class StubStateLicenseAdapter:
    state_code = "CA"
    country_code = "US"

    def __init__(self):
        self.calls = []

    def lookup_one(self, name: str, city: str):
        self.calls.append(("lookup_one", name, city))
        return []

    def fetch_bulk(self):
        self.calls.append(("fetch_bulk",))
        return []


class StubWebsiteAdapter:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def check(self, url: str, *, allow_browser_fallback: bool = True):
        self.calls.append((url, allow_browser_fallback))
        return self.result


class StubRenderer:
    def __init__(self):
        self.calls = []

    def render(self, state):
        self.calls.append((state.target_name, state.target_location))
        return f"rendered {state.target_name} in {state.target_location}"


def test_orchestrator_runs_steps_in_fixed_order():
    obdb = StubOBDBAdapter()
    state_license = StubStateLicenseAdapter()
    website = StubWebsiteAdapter(
        WebsiteSignal(
            signal="active",
            final_url="https://brew.example",
            status_code=200,
            source_url="https://brew.example",
        )
    )
    renderer = StubRenderer()

    result = BreweryRunOrchestrator(
        obdb_adapter=obdb,
        state_license_adapter=state_license,
        website_adapter=website,
        renderer=renderer,
    ).run("Auburn Ale House", "Auburn, CA")

    assert [outcome.step_id for outcome in result.step_outcomes] == [
        "obdb_lookup",
        "state_license_fetch",
        "website_check",
        "confidence",
        "diff",
        "gate",
        "render",
    ]
    assert result.obdb_record.name == "Auburn Ale House"
    assert result.rendered_output == "rendered Auburn Ale House in Auburn, CA"


def test_orchestrator_continues_after_step_error_and_preserves_state():
    obdb = StubOBDBAdapter()
    state_license = StubStateLicenseAdapter()
    website = StubWebsiteAdapter(
        StepError(
            step_id="website_check",
            message="Website requires JavaScript rendering; plain HTTP evaluation blocked.",
            source="https://brew.example",
            code="technical_blocked",
        )
    )
    renderer = StubRenderer()

    result = BreweryRunOrchestrator(
        obdb_adapter=obdb,
        state_license_adapter=state_license,
        website_adapter=website,
        renderer=renderer,
    ).run("Auburn Ale House", "Auburn, CA")

    assert result.error is not None
    assert result.error.code == "technical_blocked"
    assert result.rendered_output.startswith("rendered Auburn Ale House in Auburn, CA")
    assert result.step_outcomes[-1].step_id == "render"
