from typing import Protocol, runtime_checkable

from obdb.agent.state import StepError, WebsiteSignal


@runtime_checkable
class WebsitePort(Protocol):
    def check(
        self, url: str, *, allow_browser_fallback: bool = True
    ) -> WebsiteSignal | StepError: ...
