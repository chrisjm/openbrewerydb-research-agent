from typing import Protocol, runtime_checkable

from pydantic import BaseModel, model_validator

from obdb.agent.state import OBDBRecord, StepError


class OBDBQuery(BaseModel, frozen=True):
    """Structured brewery lookup request. Requires name + at least one location field."""

    name: str
    state: str | None = None
    city: str | None = None
    postal_code: str | None = None

    @model_validator(mode="after")
    def _require_at_least_one_location(self) -> "OBDBQuery":
        if not any([self.state, self.city, self.postal_code]):
            raise ValueError(
                "OBDBQuery requires at least one location field (state, city, or postal_code)"
            )
        return self


@runtime_checkable
class OBDBPort(Protocol):
    def lookup_one(self, query: "OBDBQuery") -> OBDBRecord | StepError | None: ...
