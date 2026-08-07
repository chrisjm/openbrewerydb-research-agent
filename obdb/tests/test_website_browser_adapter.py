from obdb.agent.state import StepError, WebsiteSignal


def test_browser_adapter_uses_checker_when_provided():
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter

    adapter = WebsiteBrowserAdapter(
        checker=lambda url: WebsiteSignal(
            signal="active",
            final_url=url,
            status_code=200,
            source_url=url,
        )
    )
    result = adapter.check("https://brew.example")
    assert result.signal == "active"


def test_browser_adapter_without_checker_returns_technical_blocked():
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter

    result = WebsiteBrowserAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert result.code == "technical_blocked"


def test_browser_adapter_checker_exception_returns_technical_blocked():
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter

    adapter = WebsiteBrowserAdapter(checker=lambda url: (_ for _ in ()).throw(RuntimeError("boom")))
    result = adapter.check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.code == "technical_blocked"
    assert "boom" in result.message


def test_browser_adapter_implements_website_port():
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter
    from obdb.ports.website_port import WebsitePort

    assert isinstance(WebsiteBrowserAdapter(), WebsitePort)
