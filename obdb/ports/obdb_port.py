from typing import Protocol, runtime_checkable

from obdb.agent.state import OBDBRecord, StepError


@runtime_checkable
class OBDBPort(Protocol):
    def lookup_one(self, name: str, location: str) -> OBDBRecord | StepError | None: ...
