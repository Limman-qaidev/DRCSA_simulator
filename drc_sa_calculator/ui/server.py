"""NiceGUI server entrypoint."""
from __future__ import annotations

from nicegui import ui

from .pages import baseline, compare_view, data_loader, scenario_builder, scenario_matrix


def create_ui(api_url: str = "http://localhost:8000") -> None:
    """Register all UI pages and start NiceGUI if executed directly."""

    data_loader.register(api_url)
    baseline.register(api_url)
    scenario_builder.register(api_url)
    scenario_matrix.register(api_url)
    compare_view.register(api_url)

    @ui.page("/")
    async def index() -> None:
        ui.label("DRC SA Calculator").classes("text-3xl font-bold mb-4")
        ui.link("Data Loader", "/data-loader")
        ui.link("Baseline", "/baseline")
        ui.link("Scenario Builder", "/scenario-builder")
        ui.link("Scenario Matrix", "/scenario-matrix")
        ui.link("Compare View", "/compare")


if __name__ == "__main__":  # pragma: no cover - manual execution
    create_ui()
    ui.run(title="DRC SA Calculator UI")
