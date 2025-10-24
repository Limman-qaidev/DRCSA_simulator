"""Domain models for DRCSA calculator."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PolicySelection:
    """Selected regulatory policy name."""

    name: str


@dataclass(frozen=True)
class Exposure:
    """Single exposure used in computations."""

    trade_id: str
    notional: float
    currency: str
    product_type: str | None = None
    exposure_class: str | None = None
    quality_step: str | None = None
    counterparty_grade: str | None = None
    lgd_grade: str | None = None
    hedging_set: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioDefinition:
    """User provided scenario definition containing exposures."""

    name: str
    description: str | None
    exposures: tuple[Exposure, ...]
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - dataclass hook
        object.__setattr__(self, "exposures", tuple(self.exposures))
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True)
class ScenarioRegistryEntry:
    """Descriptor for stored scenarios."""

    name: str
    description: str | None
    created_at: datetime
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PolicyContext:
    """Metadata about the policy used for a computation."""

    name: str
    dataset_hashes: Mapping[str, str]


@dataclass(frozen=True)
class ExposureComputation:
    """Computed risk metrics for an exposure."""

    trade_id: str
    notional: float
    risk_weight: float
    capital_charge: float
    classification_path: tuple[str, ...]
    lgd: float | None
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenarioResult:
    """Computation output for a single scenario."""

    scenario_name: str
    total_capital_charge: float
    exposures: tuple[ExposureComputation, ...]
    exposure_count: int
    total_notional: float


@dataclass(frozen=True)
class ComputationRequest:
    """Request to compute baseline and alternative scenarios."""

    policy: PolicySelection
    baseline: ScenarioDefinition
    scenarios: tuple[ScenarioDefinition, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - dataclass hook
        object.__setattr__(self, "scenarios", tuple(self.scenarios))


@dataclass(frozen=True)
class ComputationResult:
    """Result for a computation invocation."""

    policy: PolicyContext
    baseline: ScenarioResult
    scenarios: tuple[ScenarioResult, ...]
    generated_at: datetime


@dataclass(frozen=True)
class ScenarioComparison:
    """Comparison between baseline and scenario results."""

    baseline: ScenarioResult
    scenario: ScenarioResult
    delta_total_charge: float
    exposure_deltas: Mapping[str, float]


@dataclass(frozen=True)
class ScenarioMatrix:
    """Matrix view of multiple scenario outcomes."""

    baseline: ScenarioResult
    scenarios: tuple[ScenarioResult, ...]

    def iter_rows(self) -> Iterable[tuple[str, float, float]]:
        """Yield tuples of scenario name, scenario charge, and delta."""

        baseline_charge = self.baseline.total_capital_charge
        yield (self.baseline.scenario_name, baseline_charge, 0.0)
        for scenario in self.scenarios:
            delta = scenario.total_capital_charge - baseline_charge
            yield (
                scenario.scenario_name,
                scenario.total_capital_charge,
                delta,
            )


__all__ = [
    "ComputationRequest",
    "ComputationResult",
    "Exposure",
    "ExposureComputation",
    "PolicyContext",
    "PolicySelection",
    "ScenarioComparison",
    "ScenarioDefinition",
    "ScenarioMatrix",
    "ScenarioRegistryEntry",
    "ScenarioResult",
]
