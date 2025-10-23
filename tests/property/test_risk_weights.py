from __future__ import annotations

from typing import List, Tuple

import pytest
from hypothesis import given, strategies as st

from drc_sa_calculator.domain.models import (
    ComputationRequest,
    Exposure,
    PolicySelection,
    ScenarioDefinition,
)

pytestmark = pytest.mark.property


def _flatten_risk_weights(node: dict, prefix: Tuple[str, ...] = ()) -> List[Tuple[Tuple[str, ...], float]]:
    results: List[Tuple[Tuple[str, ...], float]] = []
    for key, value in node.items():
        new_prefix = prefix + (key,)
        if isinstance(value, dict):
            results.extend(_flatten_risk_weights(value, new_prefix))
        else:
            results.append((new_prefix, float(value)))
    return results


@pytest.fixture(scope="session")
def risk_weight_cases(policy_loader) -> List[Tuple[Tuple[str, ...], float]]:
    policy = policy_loader.load("BCBS_MAR")
    exposures = policy.risk_weights["exposures"]
    return _flatten_risk_weights(exposures)


@given(st.data())
def test_resolved_risk_weights_match_policy(
    calculation_engine, risk_weight_cases: List[Tuple[Tuple[str, ...], float]], data
) -> None:
    path, expected = data.draw(st.sampled_from(risk_weight_cases))
    exposure_class = path[0]
    quality_parts = path[1:]
    quality = "/".join(quality_parts)
    exposure = Exposure(
        trade_id="prop",
        notional=1.0,
        currency="USD",
        exposure_class=exposure_class,
        quality_step=quality or None,
    )
    scenario = ScenarioDefinition(name="prop", description=None, exposures=(exposure,))
    request = ComputationRequest(policy=PolicySelection("BCBS_MAR"), baseline=scenario)
    result = calculation_engine.compute(request)
    resolved = result.baseline.exposures[0].risk_weight
    assert resolved == pytest.approx(expected)
