import json as _json
import os
import re
import ssl
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx
import truststore

from obdb.agent.state import StepError, WebsiteAddress, WebsiteSignal
from obdb.ports.website_port import WebsitePort

# Use OS/browser trust store (handles AIA fetching on macOS/Windows; system certs on Linux)
_SSL_CTX = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

DEFAULT_CLOSURE_PHRASES: tuple[str, ...] = (
    "permanently closed",
    "now closed",
    "we are closed",
    "closed for good",
)
_STEP_ID = "website_check"
_TIMEOUT = 10.0

_BLOCKER_PATTERNS: tuple[tuple[str, str], ...] = (
    ("enable javascript", "Website requires JavaScript rendering; plain HTTP evaluation blocked."),
    ("attention required", "Website is blocked by anti-bot challenge."),
    ("cloudflare", "Website is blocked by anti-bot challenge."),
    ("verify you are human", "Website is blocked by anti-bot challenge."),
    ("captcha", "Website is blocked by anti-bot challenge."),
    ("sign in to continue", "Website requires authentication; plain HTTP evaluation blocked."),
    ("log in to continue", "Website requires authentication; plain HTTP evaluation blocked."),
)

_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _blocked_reason(body_text: str) -> str | None:
    for pattern, reason in _BLOCKER_PATTERNS:
        if pattern in body_text:
            return reason
    return None


def _extract_jsonld_address(html: str) -> WebsiteAddress | None:
    """Pull the first PostalAddress from any JSON-LD block on the page."""
    for m in _JSONLD_RE.finditer(html):
        try:
            data = _json.loads(m.group(1))
        except _json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            addr = item.get("address")
            if not isinstance(addr, dict):
                continue
            geo = item.get("geo") or {}
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            return WebsiteAddress(
                street=addr.get("streetAddress") or None,
                city=addr.get("addressLocality") or None,
                state=addr.get("addressRegion") or None,
                postal_code=addr.get("postalCode") or None,
                country=addr.get("addressCountry") or None,
                phone=item.get("telephone") or None,
                latitude=str(lat) if lat is not None else None,
                longitude=str(lon) if lon is not None else None,
            )
    return None


class WebsiteHttpAdapter:
    def __init__(
        self,
        closure_phrases: tuple[str, ...] = DEFAULT_CLOSURE_PHRASES,
        browser_adapter: WebsitePort | None = None,
    ):
        self._closure_phrases = closure_phrases
        self._browser_adapter = browser_adapter

    def check(self, url: str, *, allow_browser_fallback: bool = True) -> WebsiteSignal | StepError:
        header_name = os.getenv("SCRAPER_IDENTITY_HEADER_NAME", "User-Agent")
        if not header_name.strip():
            return StepError(
                step_id=_STEP_ID,
                message="Missing required scraper identity header name",
                source=url,
                code="config_error",
            )
        header_value = os.getenv("SCRAPER_IDENTITY_HEADER_VALUE")
        if not header_value:
            return StepError(
                step_id=_STEP_ID,
                message="Missing required scraper identity header value",
                source=url,
                code="config_error",
            )

        headers = {header_name: header_value}
        robots_result = self._check_robots(url, header_value, headers)
        if isinstance(robots_result, StepError):
            return self._maybe_fallback(
                url,
                robots_result,
                allow_browser_fallback=allow_browser_fallback,
            )

        try:
            resp = httpx.get(
                url, timeout=_TIMEOUT, follow_redirects=False, headers=headers, verify=_SSL_CTX
            )
        except httpx.RequestError as exc:
            return self._maybe_fallback(
                url,
                StepError(
                    step_id=_STEP_ID,
                    message=f"Request error: {exc}",
                    source=url,
                    code="technical_blocked",
                ),
                allow_browser_fallback=allow_browser_fallback,
            )

        status_code = resp.status_code
        final_url = str(resp.url)
        body_lower = resp.text.lower()

        if 300 <= status_code < 400:
            location = resp.headers.get("location")
            if location:
                final_url = str(resp.url.join(location))
            return WebsiteSignal(
                signal="redirect",
                final_url=final_url,
                status_code=status_code,
                source_url=url,
            )
        if status_code == 404:
            return WebsiteSignal(
                signal="404",
                final_url=final_url,
                status_code=status_code,
                source_url=url,
            )
        if 200 <= status_code < 300:
            blocked_reason = _blocked_reason(body_lower)
            if blocked_reason:
                return self._maybe_fallback(
                    url,
                    StepError(
                        step_id=_STEP_ID,
                        message=blocked_reason,
                        source=url,
                        code="technical_blocked",
                    ),
                    allow_browser_fallback=allow_browser_fallback,
                )
            for phrase in self._closure_phrases:
                phrase_lower = phrase.lower()
                if phrase_lower and phrase_lower in body_lower:
                    return WebsiteSignal(
                        signal="closed_keyword",
                        final_url=final_url,
                        status_code=status_code,
                        matched_phrase=phrase,
                        source_url=url,
                    )
            return WebsiteSignal(
                signal="active",
                final_url=final_url,
                status_code=status_code,
                source_url=url,
                extracted_address=_extract_jsonld_address(resp.text),
            )

        blocked_reason = _blocked_reason(body_lower)
        if blocked_reason:
            return self._maybe_fallback(
                url,
                StepError(
                    step_id=_STEP_ID,
                    message=blocked_reason,
                    source=url,
                    code="technical_blocked",
                ),
                allow_browser_fallback=allow_browser_fallback,
            )

        return self._maybe_fallback(
            url,
            StepError(
                step_id=_STEP_ID,
                message=f"Unsupported status code for website evaluation: {status_code}",
                source=url,
                code="technical_blocked",
            ),
            allow_browser_fallback=allow_browser_fallback,
        )

    def _check_robots(self, url: str, user_agent: str, headers: dict[str, str]) -> StepError | None:
        parts = urlsplit(url)
        if not parts.scheme or not parts.netloc:
            return StepError(
                step_id=_STEP_ID,
                message="Invalid website URL for robots policy evaluation",
                source=url,
                code="technical_blocked",
            )
        robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
        try:
            resp = httpx.get(
                robots_url,
                timeout=_TIMEOUT,
                follow_redirects=True,
                headers=headers,
                verify=_SSL_CTX,
            )
        except httpx.RequestError:
            # SSL/connection failure on robots.txt — assume allowed, proceed
            return None

        if resp.status_code != 200:
            return StepError(
                step_id=_STEP_ID,
                message=f"Unable to read robots.txt: HTTP {resp.status_code}",
                source=robots_url,
                code="technical_blocked",
            )

        robots_text = resp.text
        if "user-agent" not in robots_text.lower():
            return StepError(
                step_id=_STEP_ID,
                message="Invalid robots.txt format",
                source=robots_url,
                code="technical_blocked",
            )

        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(robots_text.splitlines())
        if not parser.can_fetch(user_agent, url):
            return StepError(
                step_id=_STEP_ID,
                message="robots.txt disallows crawling this URL",
                source=url,
                code="policy_blocked",
            )
        return None

    def _maybe_fallback(
        self, url: str, error: StepError, *, allow_browser_fallback: bool
    ) -> WebsiteSignal | StepError:
        if (
            allow_browser_fallback
            and error.code == "technical_blocked"
            and self._browser_adapter is not None
        ):
            return self._browser_adapter.check(url, allow_browser_fallback=False)
        return error
