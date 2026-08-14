from obdb.agent.state import BreweryRunState


class TextRenderer:
    """Plain-text summary of a brewery research run."""

    def render(self, state: BreweryRunState) -> str:
        lines = [
            f"=== {state.target_name} — {state.target_location} ===",
            "",
        ]

        rec = state.obdb_record
        if rec:
            lines += [
                "OBDB Record",
                f"  id:       {rec.id}",
                f"  name:     {rec.name}",
                f"  type:     {rec.brewery_type}",
                f"  address:  {rec.address_1}, {rec.city}, {rec.state_province} {rec.postal_code}",
                f"  website:  {rec.website_url}",
                f"  phone:    {rec.phone}",
                "",
            ]

        if state.state_license_records:
            lines.append("State License Records")
            for r in state.state_license_records:
                lines.append(f"  [{r.state_code}] {r.name} — {r.city} — status: {r.license_status}")
            lines.append("")

        sig = state.website_signal
        if sig:
            lines.append("Website Signal")
            lines.append(f"  signal:  {sig.signal}")
            if sig.signal != "unknown":
                lines.append(f"  url:     {sig.final_url}  (HTTP {sig.status_code})")
            if sig.extracted_address:
                addr = sig.extracted_address
                lines.append(
                    f"  JSON-LD: {addr.street}, {addr.city}, {addr.state} {addr.postal_code}"
                )
            lines.append("")

        if state.confidence:
            score = state.confidence.get("score")
            threshold = state.confidence.get("threshold")
            gate = (state.gate or {}).get("gate", "?")
            lines.append(f"Confidence: {score} / {threshold}  →  gate: {gate}")
            lines.append("")

        changes = (state.diff or {}).get("diff", [])
        if changes:
            lines.append("Proposed Diffs")
            for c in changes:
                src = ", ".join(c.get("evidence_refs", []))
                lines.append(
                    f"  {c['field']:20s}  {str(c['old_value']):30s} → {c['new_value']}  [{src}]"
                )
            lines.append("")

        if state.error:
            lines.append(f"⚠ Error [{state.error.step_id}]: {state.error.message}")
            lines.append("")

        return "\n".join(lines)
