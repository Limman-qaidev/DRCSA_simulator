"""Command line interface for the DRC SA calculator."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .app import schemas
from .domain.compare import compare_scenarios
from .domain.engine import DRCSACalculationEngine, PolicyDataLoader

LOGGER = logging.getLogger(__name__)


def compute_command(args: argparse.Namespace) -> int:
    """Execute the calculator for the provided scenario file."""

    logging.basicConfig(level=logging.INFO)
    scenario_path = Path(args.scenario_file)
    if not scenario_path.exists():
        LOGGER.error("Scenario file '%s' does not exist", scenario_path)
        return 1
    payload = json.loads(scenario_path.read_text(encoding="utf-8"))
    payload.setdefault("policy", args.policy)
    request_model = schemas.ComputationRequestModel.from_dict(payload)
    loader = PolicyDataLoader()
    engine = DRCSACalculationEngine(loader)
    result = engine.compute(request_model.to_domain())
    comparisons = (
        [
            compare_scenarios(result.baseline, scenario)
            for scenario in result.scenarios
        ]
        if args.include_comparisons
        else []
    )
    response = schemas.ComputationResponseModel.from_domain(
        result, comparisons
    )
    print(json.dumps(response.to_dict(), indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Default Risk Charge (SA) calculator"
    )
    parser.add_argument(
        "scenario_file",
        help="JSON file describing baseline and scenarios",
    )
    parser.add_argument(
        "--policy",
        "-p",
        required=True,
        help="Regulatory policy to apply",
    )
    parser.add_argument(
        "--include-comparisons",
        dest="include_comparisons",
        action="store_true",
        default=True,
        help="Include comparisons in the output payload",
    )
    parser.add_argument(
        "--no-include-comparisons",
        dest="include_comparisons",
        action="store_false",
        help="Exclude comparisons in the output payload",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return compute_command(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
