from collections.abc import Mapping
from typing import Any

import pytest
import schemathesis

from drc_sa_calculator.app.main import create_app
from drc_sa_calculator.domain.models import ScenarioDefinition

pytestmark = pytest.mark.contract

SCHEMA = schemathesis.from_asgi("/openapi.json", app=create_app())


def _serialise_scenario(
    scenario: ScenarioDefinition,
) -> Mapping[str, Any]:
    return {
        "name": scenario.name,
        "description": scenario.description,
        "tags": list(scenario.tags),
        "exposures": [
            {
                "trade_id": exposure.trade_id,
                "notional": exposure.notional,
                "currency": exposure.currency,
                "product_type": exposure.product_type,
                "exposure_class": exposure.exposure_class,
                "quality_step": exposure.quality_step,
                "counterparty_grade": exposure.counterparty_grade,
                "lgd_grade": exposure.lgd_grade,
                "hedging_set": exposure.hedging_set,
                "metadata": dict(exposure.metadata),
            }
            for exposure in scenario.exposures
        ],
    }


def test_compute_contract(
    baseline_scenario: ScenarioDefinition,
    stress_scenario: ScenarioDefinition,
) -> None:
    case = SCHEMA["/compute"]["post"].make_case(
        media_type="application/json",
        body={
            "policy": "BCBS_MAR",
            "baseline": _serialise_scenario(baseline_scenario),
            "scenarios": [_serialise_scenario(stress_scenario)],
        },
    )
    response = case.call_asgi()
    case.validate_response(response)
    payload = response.json()
    assert response.status_code == 200
    assert payload["result"]["baseline"]["exposure_count"] == len(
        baseline_scenario.exposures
    )


def test_reference_risk_weights_contract() -> None:
    case = SCHEMA["/reference/policies/{policy_name}/risk-weights"][
        "get"
    ].make_case(path_parameters={"policy_name": "BCBS_MAR"})
    response = case.call_asgi()
    case.validate_response(response)
    data = response.json()
    assert "exposures" in data


def test_dataset_listing_contract() -> None:
    case = SCHEMA["/datasets/policies"]["get"].make_case()
    response = case.call_asgi()
    case.validate_response(response)
    assert "BCBS_MAR" in response.json()
