"""NiceGUI page to display scenario matrix results."""

from __future__ import annotations

from nicegui import ui

from ..services import ApiClient


def register(api_url: str) -> None:
    client = ApiClient(api_url)

    @ui.page("/scenario-matrix")
    async def scenario_matrix_page() -> None:
        ui.label("Scenario Matrix").classes("text-2xl font-bold mb-4")
        status = ui.label("Loading scenarios...")
        policy_input = ui.input("Policy", value="BCBS_MAR")
        baseline_select = ui.select(options=[], label="Baseline scenario")
        scenario_select = ui.select(
            options=[], label="Comparison scenarios", multiple=True
        )
        table = ui.table(
            columns=[
                {"name": "scenario", "label": "Scenario"},
                {"name": "capital", "label": "Capital Charge"},
                {"name": "delta", "label": "Delta vs Baseline"},
            ],
            rows=[],
        )

        async def refresh() -> None:
            scenarios = await client.list_scenarios()
            names = [scenario["name"] for scenario in scenarios]
            baseline_select.options = names
            scenario_select.options = names
            status.text = f"Loaded {len(names)} scenarios"

        async def run_matrix() -> None:
            if not baseline_select.value:
                ui.notification("Select a baseline scenario", color="negative")
                return
            baseline = await client.get_scenario(baseline_select.value)
            scenario_names = scenario_select.value or []
            scenario_payloads = [
                await client.get_scenario(name) for name in scenario_names
            ]
            payload = {
                "policy": policy_input.value,
                "baseline": baseline,
                "scenarios": scenario_payloads,
            }
            response = await client.compute(payload)
            result = response.get("result", {})
            baseline_result = result.get("baseline")
            if not baseline_result:
                return
            rows = [
                {
                    "scenario": baseline_result["scenario_name"],
                    "capital": baseline_result["total_capital_charge"],
                    "delta": 0.0,
                }
            ]
            baseline_capital = baseline_result["total_capital_charge"]
            for scenario in result.get("scenarios", []):
                rows.append(
                    {
                        "scenario": scenario["scenario_name"],
                        "capital": scenario["total_capital_charge"],
                        "delta": scenario["total_capital_charge"]
                        - baseline_capital,
                    }
                )
            table.rows = rows

        ui.button("Compute matrix", on_click=run_matrix)
        ui.button("Refresh scenarios", on_click=refresh)
        await refresh()
