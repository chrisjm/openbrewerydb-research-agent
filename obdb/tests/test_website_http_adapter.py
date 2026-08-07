import httpx
import pytest

from obdb.agent.state import StepError


def test_check_returns_active_for_200_without_closure_phrase(httpx_mock):
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
    httpx_mock.add_response(url="https://brew.example", status_code=404)
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert result.signal == "404"
    assert result.status_code == 404


def test_check_returns_closed_keyword_when_phrase_matches(httpx_mock):
    httpx_mock.add_response(
        url="https://brew.example", status_code=200, text="This location is now closed."
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter(closure_phrases=("now closed",)).check("https://brew.example")
    assert result.signal == "closed_keyword"
    assert result.matched_phrase == "now closed"


def test_check_request_error_returns_step_error_with_single_attempt(httpx_mock):
    httpx_mock.add_exception(httpx.RequestError("network down"))
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.parametrize(
    "body",
    [
        "<html><body>Please enable JavaScript to continue</body></html>",
        "<html><title>Attention Required! | Cloudflare</title></html>",
        "<html><h1>Sign in to continue</h1></html>",
    ],
)
def test_check_blocked_content_returns_step_error_not_active(httpx_mock, body):
    httpx_mock.add_response(url="https://brew.example", status_code=200, text=body)
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert result.source == "https://brew.example"


def test_check_blocked_non_2xx_returns_blocker_step_error(httpx_mock):
    httpx_mock.add_response(
        url="https://brew.example",
        status_code=403,
        text="<html><title>Attention Required! | Cloudflare</title></html>",
    )
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter

    result = WebsiteHttpAdapter().check("https://brew.example")
    assert isinstance(result, StepError)
    assert result.step_id == "website_check"
    assert "anti-bot challenge" in result.message.lower()


def test_adapter_implements_website_port():
    from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
    from obdb.ports.website_port import WebsitePort

    assert isinstance(WebsiteHttpAdapter(), WebsitePort)
