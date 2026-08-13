from typing import Literal

from pydantic import BaseModel, Field

WebsiteErrorCode = Literal["policy_blocked", "technical_blocked", "config_error"]


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
    code: WebsiteErrorCode | None = None


class StateLicenseRecord(BaseModel, frozen=True):
    id: str
    name: str
    license_status: str | None = None
    address: str | None = None
    city: str | None = None
    state_code: str
    source_url: str
    fetched_at: str


class WebsiteSignal(BaseModel, frozen=True):
    signal: Literal["active", "redirect", "404", "closed_keyword"]
    final_url: str
    status_code: int
    matched_phrase: str | None = None
    source_url: str


class StepOutcome(BaseModel, frozen=True):
    step_id: str
    status: Literal["ok", "error"]
    detail: str | None = None


class BreweryRunState(BaseModel, frozen=True):
    target_name: str
    target_location: str
    obdb_record: OBDBRecord | None = None
    state_license_records: list[StateLicenseRecord] = Field(default_factory=list)
    website_signal: WebsiteSignal | None = None
    confidence: dict | None = None
    diff: dict | None = None
    gate: dict | None = None
    error: StepError | None = None
    step_outcomes: list[StepOutcome] = Field(default_factory=list)
    rendered_output: str | None = None
