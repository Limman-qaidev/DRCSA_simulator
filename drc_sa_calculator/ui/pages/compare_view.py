"""NiceGUI page for comparing scenarios against the baseline."""
from __future__ import annotations

from nicegui import ui

from ..services import ApiClient


def register(api_url: str) -> None:
    client = ApiClient(api_url)

    @ui.page("/compare")
    async def compare_page() -> None:
        ui.label("Scenario Comparison").classes("text-2xl font-bold mb-4")
        status = ui.label("Loading scenarios...")
        policy_input = ui.input("Policy", value="BCBS_MAR")
        baseline_select = ui.select(options=[], label="Baseline scenario")
        scenario_select = ui.select(options=[], label="Scenario to compare")
        delta_label = ui.label("Delta: n/a")
        table = ui.table(
            columns=[
                {"name": "trade", "label": "Trade"},
                {"name": "delta", "label": "Capital Delta"},
            ],
            rows=[],
        )

        async def refresh() -> None:
            scenarios = await client.list_scenarios()
            names = [scenario["name"] for scenario in scenarios]
            baseline_select.options = names
            scenario_select.options = names
            status.text = f"Loaded {len(names)} scenarios"

        async def run_compare() -> None:
            if not baseline_select.value or not scenario_select.value:
                ui.notification("Select both baseline and scenario", color="negative")
                return
            baseline = await client.get_scenario(baseline_select.value)
            scenario = await client.get_scenario(scenario_select.value)
            payload = {
                "policy": policy_input.value,
                "baseline": baseline,
                "scenarios": [scenario],
            }
            response = await client.compute(payload)
            comparisons = response.get("comparisons", [])
            if not comparisons:
                return
            comparison = comparisons[0]
            delta_label.text = (
                f"Delta total capital: {comparison['delta_total_charge']:.6f}"
            )
            table.rows = [
                {"trade": trade_id, "delta": delta}
                for trade_id, delta in comparison.get("exposure_deltas", {}).items()
            ]

        ui.button("Compare", on_click=run_compare)
        ui.button("Refresh scenarios", on_click=refresh)
        await refresh()
