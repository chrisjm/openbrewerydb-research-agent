from obdb.agent.orchestrator import BreweryRunOrchestrator
from obdb.agent.state import OBDBRecord, StepError, WebsiteSignal
from obdb.ports.obdb_port import OBDBQuery
from obdb.ports.state_license_port import LicenseQuery


class StubOBDBAdapter:
    def __init__(self):
        self.calls = []

    def lookup_one(self, query: OBDBQuery):
        self.calls.append(query)
        return OBDBRecord(
            id="brew-1",
            name=query.name,
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

    def lookup_one(self, query: LicenseQuery):
        self.calls.append(query)
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
    ).run("Auburn Ale House", city="Auburn", state="CA")

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


def test_orchestrator_website_unavailable_continues_pipeline():
    """technical_blocked on website is non-blocking — pipeline runs to completion."""
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
    ).run("Auburn Ale House", city="Auburn", state="CA")

    assert result.error is None
    assert result.website_signal is not None
    assert result.website_signal.signal == "unknown"
    assert result.step_outcomes[-1].step_id == "render"
    assert [o.step_id for o in result.step_outcomes] == [
        "obdb_lookup",
        "state_license_fetch",
        "website_check",
        "confidence",
        "diff",
        "gate",
        "render",
    ]


def test_orchestrator_suppresses_copyable_output_when_gate_fails():
    class GateFailRenderer:
        def render(self, state):
            return "name,city\nAuburn Ale House,Auburn"

    result = BreweryRunOrchestrator(
        obdb_adapter=StubOBDBAdapter(),
        state_license_adapter=StubStateLicenseAdapter(),
        website_adapter=StubWebsiteAdapter(
            WebsiteSignal(
                signal="active",
                final_url="https://brew.example",
                status_code=200,
                source_url="https://brew.example",
            )
        ),
        renderer=GateFailRenderer(),
        gate_step=lambda state: {"score": 0.69, "threshold": 0.7, "gate": "fail", "status": "ok"},
    ).run("Auburn Ale House", city="Auburn", state="CA")

    assert result.gate["gate"] == "fail"
    assert "Evidence-only output" in result.rendered_output
    assert "name,city" not in result.rendered_output
