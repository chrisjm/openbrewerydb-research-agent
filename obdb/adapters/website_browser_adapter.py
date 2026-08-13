from collections.abc import Callable

from obdb.agent.state import StepError, WebsiteSignal

_STEP_ID = "website_check"


class WebsiteBrowserAdapter:
    def __init__(self, checker: Callable[[str], WebsiteSignal | StepError] | None = None):
        self._checker = checker

    def check(self, url: str, *, allow_browser_fallback: bool = True) -> WebsiteSignal | StepError:
        if self._checker is None:
            return StepError(
                step_id=_STEP_ID,
                message="Browser adapter unavailable in this environment",
                source=url,
                code="technical_blocked",
            )
        # Boundary guard: injected checker is external and may throw.
        try:
            return self._checker(url)
        except Exception as exc:
            return StepError(
                step_id=_STEP_ID,
                message=f"Browser check error: {exc}",
                source=url,
                code="technical_blocked",
            )
