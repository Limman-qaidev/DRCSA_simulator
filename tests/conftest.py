"""Shared pytest fixtures for the DRCSA simulator test-suite."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pytest

from drc_sa_calculator.domain.engine import (
    DRCSACalculationEngine,
    PolicyDataLoader,
)
from drc_sa_calculator.domain.models import Exposure, ScenarioDefinition


@pytest.fixture(scope="session")
def policy_loader() -> PolicyDataLoader:
    base_path = (
        Path(__file__).resolve().parents[1] / "drc_sa_calculator" / "regdata"
    )
    return PolicyDataLoader(base_path=base_path)


@pytest.fixture(scope="session")
def policy_data(policy_loader: PolicyDataLoader):
    return policy_loader.load("BCBS_MAR")


@pytest.fixture(scope="session")
def calculation_engine(
    policy_loader: PolicyDataLoader,
) -> DRCSACalculationEngine:
    return DRCSACalculationEngine(policy_loader)


@pytest.fixture
def baseline_exposures() -> tuple[Exposure, ...]:
    return (
        Exposure(
            trade_id="T1",
            notional=1_000_000.0,
            currency="USD",
            product_type="sovereign_bond",
            exposure_class="sovereign",
            metadata={"desk": "GOV"},
        ),
        Exposure(
            trade_id="T2",
            notional=500_000.0,
            currency="USD",
            product_type="large_bank_senior",
            exposure_class="financials",
            quality_step="large_bank/senior",
            lgd_grade="senior_secured",
            metadata={"desk": "FIN"},
        ),
    )


@pytest.fixture
def stress_exposures(
    baseline_exposures: tuple[Exposure, ...],
) -> tuple[Exposure, ...]:
    baseline, bank = baseline_exposures
    stressed_bank = Exposure(
        trade_id=bank.trade_id,
        notional=bank.notional,
        currency=bank.currency,
        product_type=None,
        exposure_class=bank.exposure_class,
        quality_step=None,
        counterparty_grade="BBB",
        lgd_grade=bank.lgd_grade,
        metadata=dict(bank.metadata),
    )
    return (baseline, stressed_bank)


@pytest.fixture
def baseline_scenario(
    baseline_exposures: tuple[Exposure, ...],
) -> ScenarioDefinition:
    return ScenarioDefinition(
        name="baseline",
        description="Baseline sovereign and bank mix",
        exposures=baseline_exposures,
        tags=("baseline",),
    )


@pytest.fixture
def stress_scenario(
    stress_exposures: tuple[Exposure, ...],
) -> ScenarioDefinition:
    return ScenarioDefinition(
        name="stress",
        description="Counterparty downgrade stress",
        exposures=stress_exposures,
        tags=("stress",),
    )


@pytest.fixture
def scenario_collection(
    baseline_scenario: ScenarioDefinition, stress_scenario: ScenarioDefinition
) -> Iterable[ScenarioDefinition]:
    return (baseline_scenario, stress_scenario)
