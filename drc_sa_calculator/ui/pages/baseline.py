"""NiceGUI page for configuring the baseline scenario."""
from __future__ import annotations

from nicegui import ui

from ..services import ApiClient


def register(api_url: str) -> None:
    client = ApiClient(api_url)

    @ui.page("/baseline")
    async def baseline_page() -> None:
        ui.label("Baseline Scenario").classes("text-2xl font-bold mb-4")
        status = ui.label("Loading stored scenarios...")
        select = ui.select(options=[], label="Baseline scenario")
        table = ui.table(
            title="Exposures",
            columns=[
                {"name": "trade_id", "label": "Trade"},
                {"name": "product", "label": "Product"},
                {"name": "notional", "label": "Notional"},
                {"name": "currency", "label": "Currency"},
            ],
            rows=[],
        )

        async def refresh() -> None:
            scenarios = await client.list_scenarios()
            select.options = [scenario["name"] for scenario in scenarios]
            status.text = f"Loaded {len(scenarios)} scenarios"

        async def load_scenario() -> None:
            if not select.value:
                table.rows = []
                return
            scenario = await client.get_scenario(select.value)
            table.rows = [
                {
                    "trade_id": exposure["trade_id"],
                    "product": exposure.get("product_type") or exposure.get("exposure_class", ""),
                    "notional": exposure["notional"],
                    "currency": exposure["currency"],
                }
                for exposure in scenario["exposures"]
            ]

        select.on_change(load_scenario)
        ui.button("Refresh", on_click=refresh)
        await refresh()
