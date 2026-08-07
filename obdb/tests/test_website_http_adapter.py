import httpx
import pytest

from obdb.agent.state import StepError


@pytest.fixture(autouse=True)
def _identity_env(monkeypatch):
    monkeypatch.setenv("SCRAPER_IDENTITY_HEADER_VALUE", "obdb-research-agent-test/1.0")
    monkeypatch.delenv("SCRAPER_IDENTITY_HEADER_NAME", raising=False)


def _add_robots_allow(httpx_mock, base_url: str = "https://brew.example"):
    httpx_mock.add_response(
        url=f"{base_url}/robots.txt",
        status_code=200,
        text="User-agent: *\nAllow: /\n",
    )


def test_check_returns_active_for_200_without_closure_phrase(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example", status_code=200, text="welcome taproom open"
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert result.signal == "active"
    assert result.source_url == "https://brew.example"
    assert result.status_code == 200
    assert result.matched_phrase is None


def test_check_returns_redirect_for_3xx_no_follow(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example",
        status_code=302,
        headers={"Location": "https://brew.example/new"},
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert result.signal == "redirect"
    assert result.source_url == "https://brew.example"
    assert result.status_code == 302


def test_check_redirect_relative_location_resolves_absolute(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example/old",
        status_code=302,
        headers={"Location": "/new"},
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example/old")
    assert result.signal == "redirect"
    assert result.final_url == "https://brew.example/new"


def test_check_returns_404_signal(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(url="https://brew.example", status_code=404)
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert result.signal == "404"
    assert result.status_code == 404


def test_check_returns_closed_keyword_when_phrase_matches(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example", status_code=200, text="This location is now closed."
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter(closure_phrases=("now closed",)).check("https://brew.example")
    assert result.signal == "closed_keyword"
    assert result.matched_phrase == "now closed"


def test_check_request_error_returns_step_error_with_single_attempt(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_exception(httpx.RequestError("network down"), url="https://brew.example")
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.parametrize(
    "body",
    [
        "<html><body>Please enable JavaScript to continue</body></html>",
        "<html><title>Attention Required! | Cloudflare</title></html>",
        "<html><h1>Sign in to continue</h1></html>",
    ],
)
def test_check_blocked_content_returns_step_error_not_active(httpx_mock, body):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(url="https://brew.example", status_code=200, text=body)
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert result.source == "https://brew.example"
    assert result.code == "technical_blocked"


def test_check_blocked_non_2xx_returns_blocker_step_error(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example",
        status_code=403,
        text="<html><title>Attention Required! | Cloudflare</title></html>",
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert result.code == "technical_blocked"
    assert "anti-bot challenge" in result.message.lower()


def test_robots_disallow_returns_policy_blocked_without_page_fetch(httpx_mock):
    httpx_mock.add_response(
        url="https://brew.example/robots.txt",
        status_code=200,
        text="User-agent: *\nDisallow: /\n",
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.code == "policy_blocked"
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert str(requests[0].url) == "https://brew.example/robots.txt"


def test_missing_identity_header_value_returns_config_error(httpx_mock, monkeypatch):
    monkeypatch.delenv("SCRAPER_IDENTITY_HEADER_VALUE", raising=False)
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.code == "config_error"


def test_missing_identity_header_name_returns_config_error(monkeypatch):
    monkeypatch.setenv("SCRAPER_IDENTITY_HEADER_NAME", " ")
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.code == "config_error"


def test_unreadable_robots_returns_technical_blocked(httpx_mock):
    httpx_mock.add_response(
        url="https://brew.example/robots.txt", status_code=503, text="unavailable"
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.code == "technical_blocked"


def test_technical_block_uses_single_browser_fallback(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example",
        status_code=503,
        text="<html><title>Attention Required! | Cloudflare</title></html>",
    )
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
    from obdb.agent.state import WebsiteSignal

    browser = WebsiteBrowserAdapter(
        checker=lambda url: WebsiteSignal(
            signal="active",
            final_url=url,
            status_code=200,
            source_url=url,
        )
    )
    result = WebsiteHttpAdapter(browser_adapter=browser).check("https://brew.example")
    assert result.signal == "active"


def test_robots_technical_block_can_use_single_browser_fallback(httpx_mock):
    httpx_mock.add_response(
        url="https://brew.example/robots.txt", status_code=503, text="unavailable"
    )
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
    from obdb.agent.state import WebsiteSignal

    browser = WebsiteBrowserAdapter(
        checker=lambda url: WebsiteSignal(
            signal="active",
            final_url=url,
            status_code=200,
            source_url=url,
        )
    )
    result = WebsiteHttpAdapter(browser_adapter=browser).check("https://brew.example")
    assert result.signal == "active"


def test_fallback_passes_allow_browser_fallback_false(httpx_mock):
    _add_robots_allow(httpx_mock)
    httpx_mock.add_response(
        url="https://brew.example",
        status_code=503,
        text="<html><title>Attention Required! | Cloudflare</title></html>",
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
    from obdb.agent.state import WebsiteSignal

    class _RecordingBrowserAdapter:
        def __init__(self):
            self.allow_browser_fallback = None

        def check(self, url: str, *, allow_browser_fallback: bool = True):
            self.allow_browser_fallback = allow_browser_fallback
            return WebsiteSignal(
                signal="active",
                final_url=url,
                status_code=200,
                source_url=url,
            )

    browser = _RecordingBrowserAdapter()
    result = WebsiteHttpAdapter(browser_adapter=browser).check("https://brew.example")
    assert result.signal == "active"
    assert browser.allow_browser_fallback is False


def test_policy_or_config_error_never_uses_browser_fallback(httpx_mock, monkeypatch):
    monkeypatch.delenv("SCRAPER_IDENTITY_HEADER_VALUE", raising=False)
    from obdb.adapters.website_browser_adapter import WebsiteBrowserAdapter
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    calls = {"count": 0}

    def _checker(url: str):
        calls["count"] += 1
        return StepError(
            step_id="website_check", message="should not run", code="technical_blocked"
        )

    browser = WebsiteBrowserAdapter(checker=_checker)
    result = WebsiteHttpAdapter(browser_adapter=browser).check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.code == "config_error"
    assert calls["count"] == 0


def test_adapter_implements_website_port():
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
    from obdb.ports.website_port import WebsitePort

    assert isinstance(WebsiteHttpAdapter(), WebsitePort)
