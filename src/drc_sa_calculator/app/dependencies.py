"""FastAPI dependency providers for shared services."""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path

from ..domain.compare import compare_scenarios
from ..domain.engine import DRCSACalculationEngine, PolicyDataLoader
from ..domain.models import ScenarioComparison, ScenarioResult
from ..infrastructure.memory import InMemoryScenarioStore


@lru_cache
def _policy_loader() -> PolicyDataLoader:
    base_path = Path(__file__).resolve().parents[1] / "regdata"
    return PolicyDataLoader(base_path=base_path)


@lru_cache
def _calculation_engine() -> DRCSACalculationEngine:
    return DRCSACalculationEngine(policy_loader=_policy_loader())


_SCENARIO_STORE = InMemoryScenarioStore()


def get_policy_loader() -> PolicyDataLoader:
    return _policy_loader()


def get_engine() -> DRCSACalculationEngine:
    return _calculation_engine()


def get_scenario_store() -> InMemoryScenarioStore:
    return _SCENARIO_STORE


def build_comparisons(
    baseline: ScenarioResult,
    scenarios: Iterable[ScenarioResult],
) -> Iterable[ScenarioComparison]:
    for scenario in scenarios:
        yield compare_scenarios(baseline, scenario)
