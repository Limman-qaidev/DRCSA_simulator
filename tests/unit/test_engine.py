from __future__ import annotations

import pytest

from drc_sa_calculator.domain.models import (
    ComputationRequest,
    PolicySelection,
    ScenarioMatrix,
)


def test_exposure_capital_charge_applies_lgd(
    calculation_engine, baseline_scenario
) -> None:
    request = ComputationRequest(
        policy=PolicySelection("BCBS_MAR"), baseline=baseline_scenario
    )
    result = calculation_engine.compute(request)

    exposures = {item.trade_id: item for item in result.baseline.exposures}
    assert exposures["T1"].risk_weight == 0.2
    assert exposures["T1"].capital_charge == 1_000_000.0 * 0.2

    expected_bank_charge = 500_000.0 * 0.35 * 0.35
    assert exposures["T2"].risk_weight == 0.35
    assert exposures["T2"].lgd == 0.35
    assert exposures["T2"].capital_charge == expected_bank_charge

    assert result.baseline.total_capital_charge == pytest.approx(
        200_000.0 + expected_bank_charge
    )
    assert result.baseline.total_notional == 1_500_000.0


def test_scenario_matrix_delta(
    calculation_engine, baseline_scenario, stress_scenario
) -> None:
    request = ComputationRequest(
        policy=PolicySelection("BCBS_MAR"),
        baseline=baseline_scenario,
        scenarios=(stress_scenario,),
    )
    result = calculation_engine.compute(request)
    matrix = ScenarioMatrix(result.baseline, result.scenarios)
    rows = list(matrix.iter_rows())

    assert rows[0] == ("baseline", result.baseline.total_capital_charge, 0.0)
    stress_row = rows[1]
    assert stress_row[0] == "stress"
    assert stress_row[1] == result.scenarios[0].total_capital_charge
    assert stress_row[2] == pytest.approx(
        result.scenarios[0].total_capital_charge
        - result.baseline.total_capital_charge
    )
