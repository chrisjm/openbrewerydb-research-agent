"""
Manual end-to-end run: Jester King Brewery, Texas.
Usage: SCRAPER_IDENTITY_HEADER_VALUE="..." uv run python scripts/run_jester_king.py
"""

from obdb.adapters.obdb_api_adapter import OBDBApiAdapter
from obdb.adapters.text_renderer import TextRenderer
from obdb.adapters.tx_license_adapter import TXLicenseAdapter
from obdb.adapters.website_http_adapter import WebsiteHttpAdapter
from obdb.agent.orchestrator import BreweryRunOrchestrator

result = BreweryRunOrchestrator(
    obdb_adapter=OBDBApiAdapter(),
    state_license_adapter=TXLicenseAdapter(),
    website_adapter=WebsiteHttpAdapter(),
    renderer=TextRenderer(),
).run("Lone Pint", state="Texas")

print(result.rendered_output)
print("--- step outcomes ---")
for o in result.step_outcomes:
    print(f"  {o.step_id:25s} {o.status:6s}  {o.detail or ''}")
