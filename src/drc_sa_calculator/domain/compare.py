"""Scenario comparison utilities."""

from __future__ import annotations

import logging

from .models import ScenarioComparison, ScenarioResult

LOGGER = logging.getLogger(__name__)


def compare_scenarios(
    baseline: ScenarioResult, scenario: ScenarioResult
) -> ScenarioComparison:
    """Return comparison metrics for the baseline and scenario."""

    LOGGER.debug(
        "Comparing scenario '%s' against baseline '%s'",
        scenario.scenario_name,
        baseline.scenario_name,
    )
    exposure_deltas: dict[str, float] = {}
    baseline_map = {
        exp.trade_id: exp.capital_charge for exp in baseline.exposures
    }
    for exposure in scenario.exposures:
        base_charge = baseline_map.get(exposure.trade_id, 0.0)
        exposure_deltas[exposure.trade_id] = (
            exposure.capital_charge - base_charge
        )
    delta_total = scenario.total_capital_charge - baseline.total_capital_charge
    LOGGER.debug(
        "Scenario '%s' delta total capital charge: %.6f",
        scenario.scenario_name,
        delta_total,
    )
    return ScenarioComparison(
        baseline=baseline,
        scenario=scenario,
        delta_total_charge=delta_total,
        exposure_deltas=exposure_deltas,
    )
