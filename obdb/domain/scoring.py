from __future__ import annotations

from obdb.agent.state import BreweryRunState

DEFAULT_CONFIDENCE_THRESHOLD = 0.7


def compute_confidence(state: BreweryRunState) -> dict:
    signal_score = 0.0

    if state.obdb_record is not None:
        signal_score += 0.35
    if state.state_license_records:
        signal_score += 0.25
    if state.website_signal is not None and state.website_signal.signal != "unknown":
        signal_score += 0.25
    if state.error is None:
        signal_score += 0.15

    score = min(max(signal_score, 0.0), 1.0)
    return {
        "score": round(score, 4),
        "threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "status": "ok",
    }


def evaluate_gate(score: float, *, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> dict:
    normalized = min(max(float(score), 0.0), 1.0)
    gate = "pass" if normalized >= threshold else "fail"
    return {
        "score": round(normalized, 4),
        "threshold": threshold,
        "gate": gate,
        "status": "ok",
    }
