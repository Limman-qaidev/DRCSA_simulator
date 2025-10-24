"""NiceGUI page for loading and inspecting policy datasets."""

from __future__ import annotations

from nicegui import ui

from ..services import ApiClient


def register(api_url: str) -> None:
    client = ApiClient(api_url)

    @ui.page("/data-loader")
    async def data_loader_page() -> None:
        ui.label("Policy Data Loader").classes("text-2xl font-bold mb-4")
        status = ui.label("Fetching policies...")
        select = ui.select(options=[], label="Available policies")
        table = ui.table(
            columns=[
                {"name": "table", "label": "Dataset"},
                {"name": "hash", "label": "Hash"},
            ],
            rows=[],
        )

        async def refresh_policies() -> None:
            policies = await client.list_policies()
            select.options = policies
            if policies:
                status.text = f"Discovered {len(policies)} policy datasets"
            else:
                status.text = "No policy datasets found"

        async def load_metadata() -> None:
            policy_name = select.value
            if not policy_name:
                return
            tables = await client.get_policy_tables(policy_name)
            table.rows = [
                {"table": table_name, "hash": table_hash}
                for table_name, table_hash in sorted(tables.items())
            ]

        select.on_change(load_metadata)
        ui.button("Refresh", on_click=refresh_policies)
        await refresh_policies()
