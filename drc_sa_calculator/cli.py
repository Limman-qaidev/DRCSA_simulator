"""Command line interface for the DRC SA calculator."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import typer

from .app import schemas
from .domain.compare import compare_scenarios
from .domain.engine import DRCSACalculationEngine, PolicyDataLoader

LOGGER = logging.getLogger(__name__)

app = typer.Typer(help="Default Risk Charge (SA) calculator")


@app.command()
def compute(
    scenario_file: Path = typer.Argument(..., help="JSON file describing baseline and scenarios"),
    policy: str = typer.Option(..., "--policy", "-p", help="Regulatory policy to apply"),
    include_comparisons: bool = typer.Option(
        True,
        "--include-comparisons/--no-include-comparisons",
        help="Include comparisons in the output payload",
    ),
) -> None:
    """Execute the calculator for the provided scenario file."""

    logging.basicConfig(level=logging.INFO)
    if not scenario_file.exists():
        raise typer.BadParameter(f"Scenario file '{scenario_file}' does not exist")
    payload = json.loads(scenario_file.read_text(encoding="utf-8"))
    payload.setdefault("policy", policy)
    request_model = schemas.ComputationRequestModel.parse_obj(payload)
    loader = PolicyDataLoader()
    engine = DRCSACalculationEngine(loader)
    result = engine.compute(request_model.to_domain())
    comparisons = (
        [compare_scenarios(result.baseline, scenario) for scenario in result.scenarios]
        if include_comparisons
        else []
    )
    response = schemas.ComputationResponseModel.from_domain(result, comparisons)
    typer.echo(json.dumps(response.dict(), indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    app()
