from __future__ import annotations

from collections.abc import Callable

from obdb.agent.state import BreweryRunState, StepError, StepOutcome
from obdb.domain.scoring import DEFAULT_CONFIDENCE_THRESHOLD, compute_confidence, evaluate_gate


class BreweryRunOrchestrator:
    def __init__(
        self,
        *,
        obdb_adapter,
        state_license_adapter,
        website_adapter,
        renderer,
        score_step: Callable[[BreweryRunState], dict] | None = None,
        diff_step: Callable[[BreweryRunState], dict] | None = None,
        gate_step: Callable[[BreweryRunState], dict] | None = None,
    ):
        self._obdb_adapter = obdb_adapter
        self._state_license_adapter = state_license_adapter
        self._website_adapter = website_adapter
        self._renderer = renderer
        self._score_step = score_step or (lambda state: compute_confidence(state))
        self._diff_step = diff_step or (lambda state: {"diff": [], "status": "ok"})
        self._gate_step = gate_step or (
            lambda state: evaluate_gate(
                self._score_step(state)["score"],
                threshold=DEFAULT_CONFIDENCE_THRESHOLD,
            )
        )

    def run(self, name: str, location: str) -> BreweryRunState:
        state = BreweryRunState(target_name=name, target_location=location)

        state = self._run_step(state, "obdb_lookup", self._lookup_obdb)
        if state.error is not None:
            return self._finalize(state)

        state = self._run_step(state, "state_license_fetch", self._fetch_state_license)
        if state.error is not None:
            return self._finalize(state)

        state = self._run_step(state, "website_check", self._check_website)
        if state.error is not None:
            return self._finalize(state)

        state = self._run_step(state, "confidence", self._score)
        if state.error is not None:
            return self._finalize(state)

        state = self._run_step(state, "diff", self._diff)
        if state.error is not None:
            return self._finalize(state)

        state = self._run_step(state, "gate", self._gate)
        if state.error is not None:
            return self._finalize(state)

        return self._run_step(state, "render", self._render)

    def _run_step(self, state: BreweryRunState, step_id: str, step_fn):
        try:
            next_state = step_fn(state)
        except Exception as exc:  # pragma: no cover - defensive guard
            next_state = state.model_copy(
                update={
                    "error": StepError(
                        step_id=step_id,
                        message=str(exc),
                        source=None,
                        code="technical_blocked",
                    ),
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(step_id=step_id, status="error", detail=str(exc)),
                    ],
                }
            )
        return next_state

    def _lookup_obdb(self, state: BreweryRunState) -> BreweryRunState:
        record = self._obdb_adapter.lookup_one(state.target_name, state.target_location)
        if isinstance(record, StepError):
            return state.model_copy(
                update={
                    "error": record,
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(step_id="obdb_lookup", status="error", detail=record.message),
                    ],
                }
            )
        if record is None:
            message = f"No OBDB record found for {state.target_name} in {state.target_location}"
            return state.model_copy(
                update={
                    "error": StepError(
                        step_id="obdb_lookup",
                        message=message,
                        source=None,
                        code="technical_blocked",
                    ),
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(step_id="obdb_lookup", status="error", detail=message),
                    ],
                }
            )
        return state.model_copy(
            update={
                "obdb_record": record,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(step_id="obdb_lookup", status="ok", detail="OBDB lookup succeeded"),
                ],
            }
        )

    def _fetch_state_license(self, state: BreweryRunState) -> BreweryRunState:
        city_name = state.target_location.split(",")[0].strip()
        result = self._state_license_adapter.lookup_one(state.target_name, city_name)
        if isinstance(result, StepError):
            return state.model_copy(
                update={
                    "error": result,
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(
                            step_id="state_license_fetch",
                            status="error",
                            detail=result.message,
                        ),
                    ],
                }
            )
        return state.model_copy(
            update={
                "state_license_records": result,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(
                        step_id="state_license_fetch",
                        status="ok",
                        detail="State license lookup succeeded",
                    ),
                ],
            }
        )

    def _check_website(self, state: BreweryRunState) -> BreweryRunState:
        if state.obdb_record is None or not state.obdb_record.website_url:
            return state.model_copy(
                update={
                    "error": StepError(
                        step_id="website_check",
                        message="No website URL available",
                        source=None,
                        code="technical_blocked",
                    ),
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(
                            step_id="website_check",
                            status="error",
                            detail="No website URL available",
                        ),
                    ],
                }
            )

        result = self._website_adapter.check(state.obdb_record.website_url)
        if isinstance(result, StepError):
            return state.model_copy(
                update={
                    "error": result,
                    "website_signal": None,
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(step_id="website_check", status="error", detail=result.message),
                    ],
                }
            )
        return state.model_copy(
            update={
                "website_signal": result,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(
                        step_id="website_check",
                        status="ok",
                        detail="Website check succeeded",
                    ),
                ],
            }
        )

    def _score(self, state: BreweryRunState) -> BreweryRunState:
        payload = self._score_step(state)
        return state.model_copy(
            update={
                "confidence": payload,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(step_id="confidence", status="ok", detail="Confidence computed"),
                ],
            }
        )

    def _diff(self, state: BreweryRunState) -> BreweryRunState:
        payload = self._diff_step(state)
        return state.model_copy(
            update={
                "diff": payload,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(step_id="diff", status="ok", detail="Diff computed"),
                ],
            }
        )

    def _gate(self, state: BreweryRunState) -> BreweryRunState:
        payload = self._gate_step(state)
        return state.model_copy(
            update={
                "gate": payload,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(step_id="gate", status="ok", detail="Gate evaluated"),
                ],
            }
        )

    def _render(self, state: BreweryRunState) -> BreweryRunState:
        output = self._render_output(state)
        return state.model_copy(
            update={
                "rendered_output": output,
                "step_outcomes": [
                    *state.step_outcomes,
                    StepOutcome(step_id="render", status="ok", detail="Rendered output"),
                ],
            }
        )

    def _render_output(self, state: BreweryRunState) -> str:
        gate = state.gate or {}
        if isinstance(gate, dict) and gate.get("gate") == "fail":
            return self._render_evidence_only(state)
        return self._renderer.render(state)

    def _render_evidence_only(self, state: BreweryRunState) -> str:
        lines = [
            "Evidence-only output",
            "",
            f"Target: {state.target_name} in {state.target_location}",
        ]
        if state.obdb_record and state.obdb_record.website_url:
            lines.append(f"Website: {state.obdb_record.website_url}")
        if state.website_signal is not None:
            lines.append(
                f"Website signal: {state.website_signal.signal} "
                f"(status {state.website_signal.status_code})"
            )
        if state.confidence is not None:
            lines.append(
                "Confidence: "
                f"{state.confidence.get('score')} / threshold "
                f"{state.confidence.get('threshold')}"
            )
        if state.error is not None:
            lines.append(f"Step error: {state.error.message}")
        lines.append("")
        lines.append("No copyable CSV is available because the confidence gate failed.")
        return "\n".join(lines)

    def _finalize(self, state: BreweryRunState) -> BreweryRunState:
        if state.step_outcomes and state.step_outcomes[-1].step_id != "render":
            renderer_output = self._render_output(state)
            return state.model_copy(
                update={
                    "rendered_output": renderer_output,
                    "step_outcomes": [
                        *state.step_outcomes,
                        StepOutcome(
                            step_id="render",
                            status="ok",
                            detail="Rendered final error state",
                        ),
                    ],
                }
            )
        return state
