"""Pydantic schemas bridging HTTP/CLI interfaces with domain models."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime

from pydantic import BaseModel, Field, validator

from ..domain import models


class ExposureModel(BaseModel):
    trade_id: str
    notional: float
    currency: str
    product_type: str | None = None
    exposure_class: str | None = None
    quality_step: str | None = None
    counterparty_grade: str | None = None
    lgd_grade: str | None = None
    hedging_set: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @validator("notional")
    def validate_notional(
        cls, value: float
    ) -> float:  # noqa: D401 - pydantic signature
        """Ensure notional is positive."""

        if value <= 0:
            raise ValueError("notional must be positive")
        return value

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
            metadata=self.metadata,
        )

    @classmethod
    def from_domain(
        cls, exposure: models.ExposureComputation
    ) -> ExposureModel:
        return cls(
            trade_id=exposure.trade_id,
            notional=exposure.notional,
            currency="",  # Computation results do not currently track currency
            metadata=dict(exposure.metadata),
        )


class ScenarioModel(BaseModel):
    name: str
    description: str | None = None
    tags: Sequence[str] = Field(default_factory=tuple)
    exposures: Sequence[ExposureModel]
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
            exposures=[
                ExposureModel(**exposure.__dict__)
                for exposure in scenario.exposures
            ],
            created_at=scenario.created_at,
        )


class ScenarioSummaryModel(BaseModel):
    name: str
    description: str | None
    created_at: datetime
    tags: Sequence[str]


class PolicySummaryModel(BaseModel):
    name: str
    tables: Mapping[str, str]


class ComputationRequestModel(BaseModel):
    policy_name: str = Field(..., alias="policy")
    baseline: ScenarioModel
    scenarios: Sequence[ScenarioModel] = Field(default_factory=tuple)

    class Config:
        allow_population_by_field_name = True

    def to_domain(self) -> models.ComputationRequest:
        return models.ComputationRequest(
            policy=models.PolicySelection(name=self.policy_name),
            baseline=self.baseline.to_domain(),
            scenarios=tuple(
                scenario.to_domain() for scenario in self.scenarios
            ),
        )


class ExposureComputationModel(BaseModel):
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


class ScenarioResultModel(BaseModel):
    scenario_name: str
    total_capital_charge: float
    exposure_count: int
    total_notional: float
    exposures: Sequence[ExposureComputationModel]

    @classmethod
    def from_domain(cls, result: models.ScenarioResult) -> ScenarioResultModel:
        return cls(
            scenario_name=result.scenario_name,
            total_capital_charge=result.total_capital_charge,
            exposure_count=result.exposure_count,
            total_notional=result.total_notional,
            exposures=[
                ExposureComputationModel.from_domain(exposure)
                for exposure in result.exposures
            ],
        )


class ComputationResultModel(BaseModel):
    policy: Mapping[str, object]
    baseline: ScenarioResultModel
    scenarios: Sequence[ScenarioResultModel]
    generated_at: datetime

    @classmethod
    def from_domain(
        cls, result: models.ComputationResult
    ) -> ComputationResultModel:
        return cls(
            policy={
                "name": result.policy.name,
                "hashes": result.policy.dataset_hashes,
            },
            baseline=ScenarioResultModel.from_domain(result.baseline),
            scenarios=[
                ScenarioResultModel.from_domain(item)
                for item in result.scenarios
            ],
            generated_at=result.generated_at,
        )


class ScenarioComparisonModel(BaseModel):
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


class ComputationResponseModel(BaseModel):
    result: ComputationResultModel
    comparisons: Sequence[ScenarioComparisonModel] = Field(
        default_factory=list
    )

    @classmethod
    def from_domain(
        cls,
        result: models.ComputationResult,
        comparisons: Iterable[models.ScenarioComparison],
    ) -> ComputationResponseModel:
        return cls(
            result=ComputationResultModel.from_domain(result),
            comparisons=[
                ScenarioComparisonModel.from_domain(comparison)
                for comparison in comparisons
            ],
        )
