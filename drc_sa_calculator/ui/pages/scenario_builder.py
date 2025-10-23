"""NiceGUI page for creating and editing scenarios."""
from __future__ import annotations

from typing import List

from nicegui import ui

from ..services import ApiClient


def register(api_url: str) -> None:
    client = ApiClient(api_url)

    @ui.page("/scenario-builder")
    async def scenario_builder_page() -> None:
        ui.label("Scenario Builder").classes("text-2xl font-bold mb-4")
        name_input = ui.input("Scenario name")
        description_input = ui.textarea("Description")
        tags_input = ui.input("Tags (comma separated)")

        exposures: List[dict] = []
        table = ui.table(
            title="Exposures",
            columns=[
                {"name": "trade_id", "label": "Trade"},
                {"name": "product_type", "label": "Product"},
                {"name": "notional", "label": "Notional"},
                {"name": "currency", "label": "Currency"},
            ],
            rows=[],
        )

        trade_id_input = ui.input("Trade ID")
        product_input = ui.input("Product type")
        exposure_class_input = ui.input("Exposure class")
        quality_input = ui.input("Quality step")
        notional_input = ui.number("Notional", value=0.0)
        currency_input = ui.input("Currency", value="USD")

        async def refresh_table() -> None:
            table.rows = exposures.copy()

        async def add_exposure() -> None:
            if not trade_id_input.value or (notional_input.value or 0.0) <= 0:
                ui.notification("Trade ID and positive notional are required", color="negative")
                return
            exposures.append(
                {
                    "trade_id": trade_id_input.value,
                    "product_type": product_input.value or None,
                    "exposure_class": exposure_class_input.value or None,
                    "quality_step": quality_input.value or None,
                    "notional": notional_input.value or 0.0,
                    "currency": currency_input.value or "USD",
                }
            )
            await refresh_table()
            for field in (trade_id_input, product_input, exposure_class_input, quality_input):
                field.value = ""
            notional_input.value = 0.0

        async def save_scenario() -> None:
            if not exposures:
                ui.notification("Add at least one exposure", color="negative")
                return
            payload = {
                "name": name_input.value,
                "description": description_input.value or None,
                "tags": [tag.strip() for tag in (tags_input.value or "").split(",") if tag.strip()],
                "exposures": exposures,
            }
            saved = await client.save_scenario(name_input.value, payload)
            ui.notification(f"Scenario '{saved['name']}' saved")

        ui.button("Add exposure", on_click=add_exposure)
        ui.button("Save scenario", on_click=save_scenario)
        await refresh_table()
