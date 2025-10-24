"""Schema utilities implemented with stdlib dataclasses."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..domain import models


def _ensure_positive(name: str, value: float) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _serialise_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items()}


@dataclass(slots=True)
class ExposureModel:
    trade_id: str
    notional: float
    currency: str
    product_type: str | None = None
    exposure_class: str | None = None
    quality_step: str | None = None
    counterparty_grade: str | None = None
    lgd_grade: str | None = None
    hedging_set: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.notional = _ensure_positive("notional", float(self.notional))

    def to_domain(self) -> models.Exposure:
        return models.Exposure(
            trade_id=self.trade_id,
            notional=self.notional,
            currency=self.currency,
            product_type=self.product_type,
            exposure_class=self.exposure_class,
            quality_step=self.quality_step,
            counterparty_grade=self.counterparty_grade,
            lgd_grade=self.lgd_grade,
            hedging_set=self.hedging_set,
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_domain(cls, exposure: models.Exposure) -> ExposureModel:
        return cls(
            trade_id=exposure.trade_id,
            notional=exposure.notional,
            currency=exposure.currency,
            product_type=exposure.product_type,
            exposure_class=exposure.exposure_class,
            quality_step=exposure.quality_step,
            counterparty_grade=exposure.counterparty_grade,
            lgd_grade=exposure.lgd_grade,
            hedging_set=exposure.hedging_set,
            metadata=dict(exposure.metadata),
        )

    @classmethod
    def from_result(
        cls, exposure: models.ExposureComputation
    ) -> ExposureModel:
        return cls(
            trade_id=exposure.trade_id,
            notional=exposure.notional,
            currency="",
            metadata=dict(exposure.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "notional": self.notional,
            "currency": self.currency,
            "product_type": self.product_type,
            "exposure_class": self.exposure_class,
            "quality_step": self.quality_step,
            "counterparty_grade": self.counterparty_grade,
            "lgd_grade": self.lgd_grade,
            "hedging_set": self.hedging_set,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class ScenarioModel:
    name: str
    description: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    exposures: tuple[ExposureModel, ...] = field(default_factory=tuple)
    created_at: datetime | None = None

    def to_domain(self) -> models.ScenarioDefinition:
        exposures = tuple(exposure.to_domain() for exposure in self.exposures)
        created_at = self.created_at or datetime.utcnow()
        return models.ScenarioDefinition(
            name=self.name,
            description=self.description,
            exposures=exposures,
            created_at=created_at,
            tags=tuple(self.tags),
        )

    @classmethod
    def from_domain(cls, scenario: models.ScenarioDefinition) -> ScenarioModel:
        return cls(
            name=scenario.name,
            description=scenario.description,
            tags=scenario.tags,
            exposures=tuple(
                ExposureModel.from_domain(exposure)
                for exposure in scenario.exposures
            ),
            created_at=scenario.created_at,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ScenarioModel:
        exposures = tuple(
            ExposureModel(**exposure)
            for exposure in payload.get("exposures", [])
        )
        tags = tuple(payload.get("tags", ()))
        created_raw = payload.get("created_at")
        created_at = (
            datetime.fromisoformat(created_raw)
            if isinstance(created_raw, str)
            else created_raw
        )
        return cls(
            name=str(payload["name"]),
            description=payload.get("description"),
            tags=tags,
            exposures=exposures,
            created_at=created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "tags": list(self.tags),
            "exposures": [exposure.to_dict() for exposure in self.exposures],
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }


@dataclass(slots=True)
class ScenarioSummaryModel:
    name: str
    description: str | None
    created_at: datetime
    tags: tuple[str, ...]

    @classmethod
    def from_domain(
        cls, scenario: models.ScenarioDefinition | models.ScenarioRegistryEntry
    ) -> ScenarioSummaryModel:
        return cls(
            name=scenario.name,
            description=scenario.description,
            created_at=scenario.created_at,
            tags=scenario.tags,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "tags": list(self.tags),
        }


@dataclass(slots=True)
class PolicySummaryModel:
    name: str
    tables: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "tables": _serialise_mapping(self.tables)}


@dataclass(slots=True)
class ComputationRequestModel:
    policy_name: str
    baseline: ScenarioModel
    scenarios: tuple[ScenarioModel, ...] = field(default_factory=tuple)

    def to_domain(self) -> models.ComputationRequest:
        return models.ComputationRequest(
            policy=models.PolicySelection(self.policy_name),
            baseline=self.baseline.to_domain(),
            scenarios=tuple(
                scenario.to_domain() for scenario in self.scenarios
            ),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ComputationRequestModel:
        baseline = ScenarioModel.from_dict(payload["baseline"])
        scenarios = tuple(
            ScenarioModel.from_dict(item)
            for item in payload.get("scenarios", [])
        )
        policy = str(payload.get("policy") or payload.get("policy_name"))
        return cls(policy_name=policy, baseline=baseline, scenarios=scenarios)


@dataclass(slots=True)
class ExposureComputationModel:
    trade_id: str
    notional: float
    risk_weight: float
    capital_charge: float
    classification_path: Sequence[str]
    lgd: float | None
    metadata: Mapping[str, str]

    @classmethod
    def from_domain(
        cls, exposure: models.ExposureComputation
    ) -> ExposureComputationModel:
        return cls(
            trade_id=exposure.trade_id,
            notional=exposure.notional,
            risk_weight=exposure.risk_weight,
            capital_charge=exposure.capital_charge,
            classification_path=exposure.classification_path,
            lgd=exposure.lgd,
            metadata=exposure.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "notional": self.notional,
            "risk_weight": self.risk_weight,
            "capital_charge": self.capital_charge,
            "classification_path": list(self.classification_path),
            "lgd": self.lgd,
            "metadata": _serialise_mapping(self.metadata),
        }


@dataclass(slots=True)
class ScenarioResultModel:
    scenario_name: str
    total_capital_charge: float
    exposure_count: int
    total_notional: float
    exposures: tuple[ExposureComputationModel, ...]

    @classmethod
    def from_domain(cls, result: models.ScenarioResult) -> ScenarioResultModel:
        return cls(
            scenario_name=result.scenario_name,
            total_capital_charge=result.total_capital_charge,
            exposure_count=result.exposure_count,
            total_notional=result.total_notional,
            exposures=tuple(
                ExposureComputationModel.from_domain(exposure)
                for exposure in result.exposures
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "total_capital_charge": self.total_capital_charge,
            "exposure_count": self.exposure_count,
            "total_notional": self.total_notional,
            "exposures": [exposure.to_dict() for exposure in self.exposures],
        }


@dataclass(slots=True)
class ComputationResultModel:
    policy: Mapping[str, Any]
    baseline: ScenarioResultModel
    scenarios: tuple[ScenarioResultModel, ...]
    generated_at: datetime

    @classmethod
    def from_domain(
        cls, result: models.ComputationResult
    ) -> ComputationResultModel:
        return cls(
            policy={
                "name": result.policy.name,
                "hashes": _serialise_mapping(result.policy.dataset_hashes),
            },
            baseline=ScenarioResultModel.from_domain(result.baseline),
            scenarios=tuple(
                ScenarioResultModel.from_domain(item)
                for item in result.scenarios
            ),
            generated_at=result.generated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "baseline": self.baseline.to_dict(),
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass(slots=True)
class ScenarioComparisonModel:
    scenario_name: str
    delta_total_charge: float
    exposure_deltas: Mapping[str, float]

    @classmethod
    def from_domain(
        cls, comparison: models.ScenarioComparison
    ) -> ScenarioComparisonModel:
        return cls(
            scenario_name=comparison.scenario.scenario_name,
            delta_total_charge=comparison.delta_total_charge,
            exposure_deltas=comparison.exposure_deltas,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "delta_total_charge": self.delta_total_charge,
            "exposure_deltas": dict(self.exposure_deltas),
        }


@dataclass(slots=True)
class ComputationResponseModel:
    result: ComputationResultModel
    comparisons: tuple[ScenarioComparisonModel, ...]

    @classmethod
    def from_domain(
        cls,
        result: models.ComputationResult,
        comparisons: Iterable[models.ScenarioComparison],
    ) -> ComputationResponseModel:
        response_comparisons = tuple(
            ScenarioComparisonModel.from_domain(comparison)
            for comparison in comparisons
        )
        return cls(
            result=ComputationResultModel.from_domain(result),
            comparisons=response_comparisons,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.to_dict(),
            "comparisons": [item.to_dict() for item in self.comparisons],
        }


__all__ = [
    "ComputationRequestModel",
    "ComputationResponseModel",
    "ExposureModel",
    "PolicySummaryModel",
    "ScenarioModel",
    "ScenarioResultModel",
    "ScenarioSummaryModel",
    "ScenarioComparisonModel",
]
