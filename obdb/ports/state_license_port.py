from typing import Protocol, runtime_checkable

from obdb.agent.state import StateLicenseRecord, StepError


@runtime_checkable
class StateLicensePort(Protocol):
    state_code: str

    def lookup_one(self, name: str, city: str) -> list[StateLicenseRecord] | StepError: ...

    def fetch_bulk(self) -> list[StateLicenseRecord] | StepError: ...
