from pydantic import BaseModel


class OBDBRecord(BaseModel, frozen=True):
    id: str
    name: str
    brewery_type: str | None = None
    address_1: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    country: str | None = None
    website_url: str | None = None
    phone: str | None = None
    longitude: str | None = None
    latitude: str | None = None


class StepError(BaseModel, frozen=True):
    step_id: str
    message: str
    source: str | None = None
