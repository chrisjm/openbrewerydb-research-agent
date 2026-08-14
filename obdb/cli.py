"""Slim CLI: research one brewery end-to-end.

Usage:
    SCRAPER_IDENTITY_HEADER_VALUE="..." uv run obdb-run "<name>" \
        --state <CA|CO|TX> [--city ...] [--postal ...]
"""

import argparse
import sys

from obdb.adapters.ca_license_adapter import CALicenseAdapter
from obdb.adapters.co_license_adapter import COLicenseAdapter
from obdb.adapters.obdb_api_adapter import OBDBApiAdapter
from obdb.adapters.text_renderer import TextRenderer
from obdb.adapters.tx_license_adapter import TXLicenseAdapter
from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
from obdb.agent.orchestrator import BreweryRunOrchestrator

# 2-letter code → license adapter class. Each adapter carries its own
# state_name (full spelling for OBDB's by_state filter) and country_code,
# so this registry is the only place to touch when a new state ships.
_LICENSE_ADAPTERS = {
    "CA": CALicenseAdapter,
    "CO": COLicenseAdapter,
    "TX": TXLicenseAdapter,
}


def _resolve_state(state_code: str):
    """Return (adapter_class, full_state_name) for a 2-letter state code."""
    cls = _LICENSE_ADAPTERS.get(state_code.upper())
    if cls is None:
        supported = ", ".join(sorted(_LICENSE_ADAPTERS))
        sys.exit(f"Unsupported state {state_code!r}. License adapter available for: {supported}.")
    return cls, cls.state_name


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="obdb-run",
        description="Research one brewery: OBDB + state license + website → confidence + diff.",
    )
    parser.add_argument("name", help="Brewery name to look up in OBDB.")
    parser.add_argument("--state", required=True, help="Two-letter state code (CA, CO, TX).")
    parser.add_argument("--city", default=None, help="City to narrow OBDB + license lookup.")
    parser.add_argument(
        "--postal", dest="postal_code", default=None, help="Postal code to narrow OBDB."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    license_adapter_cls, state_name = _resolve_state(args.state)

    result = BreweryRunOrchestrator(
        obdb_adapter=OBDBApiAdapter(),
        state_license_adapter=license_adapter_cls(),
        website_adapter=WebsiteHttpAdapter(),
        renderer=TextRenderer(),
    ).run(args.name, state=state_name, city=args.city, postal_code=args.postal_code)

    print(result.rendered_output)
    print("--- step outcomes ---")
    for o in result.step_outcomes:
        print(f"  {o.step_id:25s} {o.status:6s}  {o.detail or ''}")

    return 0 if result.error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
