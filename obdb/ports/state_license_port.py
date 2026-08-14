from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from obdb.agent.state import StateLicenseRecord, StepError


class LicenseQuery(BaseModel, frozen=True):
    """Structured license lookup request. Name required; city narrows results when provided."""

    name: str
    city: str | None = None


@runtime_checkable
class StateLicensePort(Protocol):
    state_code: str
    country_code: str

    def lookup_one(self, query: "LicenseQuery") -> list[StateLicenseRecord] | StepError: ...

    def fetch_bulk(self) -> list[StateLicenseRecord] | StepError: ...
