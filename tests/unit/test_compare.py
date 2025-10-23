from __future__ import annotations

import pytest

from drc_sa_calculator.domain.compare import compare_scenarios
from drc_sa_calculator.domain.models import ComputationRequest, PolicySelection


def test_compare_scenarios_reports_deltas(
    calculation_engine, baseline_scenario, stress_scenario
) -> None:
    request = ComputationRequest(
        policy=PolicySelection("BCBS_MAR"),
        baseline=baseline_scenario,
        scenarios=(stress_scenario,),
    )
    result = calculation_engine.compute(request)
    comparison = compare_scenarios(result.baseline, result.scenarios[0])

    assert comparison.scenario.scenario_name == "stress"
    assert comparison.delta_total_charge == pytest.approx(
        result.scenarios[0].total_capital_charge - result.baseline.total_capital_charge
    )
    assert set(comparison.exposure_deltas) == {"T1", "T2"}
    assert comparison.exposure_deltas["T1"] == pytest.approx(0.0)

    stress_charge = next(
        exp.capital_charge for exp in result.scenarios[0].exposures if exp.trade_id == "T2"
    )
    baseline_charge = next(
        exp.capital_charge for exp in result.baseline.exposures if exp.trade_id == "T2"
    )
    assert comparison.exposure_deltas["T2"] == pytest.approx(stress_charge - baseline_charge)
