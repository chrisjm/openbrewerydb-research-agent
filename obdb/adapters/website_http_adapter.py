import httpx

from obdb.agent.state import StepError, WebsiteSignal

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


def _blocked_reason(body_text: str) -> str | None:
    for pattern, reason in _BLOCKER_PATTERNS:
        if pattern in body_text:
            return reason
    return None


class WebsiteHttpAdapter:
    def __init__(self, closure_phrases: tuple[str, ...] = DEFAULT_CLOSURE_PHRASES):
        self._closure_phrases = closure_phrases

    def check(self, url: str) -> WebsiteSignal | StepError:
        try:
            resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=False)
        except httpx.RequestError as exc:
            return StepError(step_id=_STEP_ID, message=f"Request error: {exc}", source=url)

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
                return StepError(step_id=_STEP_ID, message=blocked_reason, source=url)

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
            )

        blocked_reason = _blocked_reason(body_lower)
        if blocked_reason:
            return StepError(step_id=_STEP_ID, message=blocked_reason, source=url)

        return StepError(
            step_id=_STEP_ID,
            message=f"Unsupported status code for website evaluation: {status_code}",
            source=url,
        )
