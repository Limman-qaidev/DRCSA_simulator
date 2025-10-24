"""Computation engine for the DRCSA simulator."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime

from .. import models
from ..rules import validate_scenarios
from .policy import PolicyData, PolicyDataLoader

LOGGER = logging.getLogger(__name__)


class RiskWeightResolutionError(RuntimeError):
    """Raised when a risk weight cannot be resolved for an exposure."""


class DRCSACalculationEngine:
    """Core calculator used to compute capital charges for scenarios."""

    def __init__(self, policy_loader: PolicyDataLoader) -> None:
        self._policy_loader = policy_loader

    def compute(
        self, request: models.ComputationRequest
    ) -> models.ComputationResult:
        """Compute baseline and alternative scenario results."""

        LOGGER.info("Starting computation for policy %s", request.policy.name)
        validate_scenarios((request.baseline, *request.scenarios))
        policy = self._policy_loader.load(request.policy.name)
        baseline = self._compute_scenario(policy, request.baseline)
        scenarios = tuple(
            self._compute_scenario(policy, scenario)
            for scenario in request.scenarios
        )
        result = models.ComputationResult(
            policy=models.PolicyContext(
                name=policy.name, dataset_hashes=policy.hashes
            ),
            baseline=baseline,
            scenarios=scenarios,
            generated_at=datetime.utcnow(),
        )
        LOGGER.info(
            "Computation for policy %s produced %s alternative scenarios",
            request.policy.name,
            len(scenarios),
        )
        return result

    def _compute_scenario(
        self, policy: PolicyData, scenario: models.ScenarioDefinition
    ) -> models.ScenarioResult:
        LOGGER.debug(
            "Computing scenario '%s' under policy '%s'",
            scenario.name,
            policy.name,
        )
        exposure_results = [
            self._compute_exposure(policy, exposure)
            for exposure in scenario.exposures
        ]
        total_capital = sum(item.capital_charge for item in exposure_results)
        total_notional = sum(item.notional for item in exposure_results)
        LOGGER.debug(
            "Scenario '%s' total capital %.6f from %s exposures",
            scenario.name,
            total_capital,
            len(exposure_results),
        )
        return models.ScenarioResult(
            scenario_name=scenario.name,
            total_capital_charge=total_capital,
            exposures=tuple(exposure_results),
            exposure_count=len(exposure_results),
            total_notional=total_notional,
        )

    def _compute_exposure(
        self, policy: PolicyData, exposure: models.Exposure
    ) -> models.ExposureComputation:
        classification_path = self._resolve_classification(policy, exposure)
        risk_weight = self._risk_weight_from_policy(
            policy, classification_path
        )
        lgd = self._resolve_lgd(policy, exposure)
        capital_charge = exposure.notional * risk_weight
        if lgd is not None:
            capital_charge *= lgd
        LOGGER.debug(
            "Exposure %s classified as %s with risk weight %.6f and LGD %s",
            exposure.trade_id,
            "/".join(classification_path),
            risk_weight,
            f"{lgd:.6f}" if lgd is not None else "<not set>",
        )
        return models.ExposureComputation(
            trade_id=exposure.trade_id,
            notional=exposure.notional,
            risk_weight=risk_weight,
            capital_charge=capital_charge,
            classification_path=classification_path,
            lgd=lgd,
            metadata=dict(exposure.metadata),
        )

    def _resolve_classification(
        self, policy: PolicyData, exposure: models.Exposure
    ) -> tuple[str, ...]:
        exposure_class = exposure.exposure_class
        quality = exposure.quality_step
        if exposure.product_type and (not exposure_class or not quality):
            mapping = policy.mappings.get("product_mappings", {})
            product_map = mapping.get(exposure.product_type)
            if product_map:
                exposure_class = exposure_class or product_map.get("exposure")
                quality = quality or product_map.get("quality_step")
        if exposure.counterparty_grade and not quality:
            grade_mapping = policy.mappings.get("counterparty_grades", {})
            quality = grade_mapping.get(exposure.counterparty_grade)
        if not exposure_class:
            message = (
                f"Exposure {exposure.trade_id} missing exposure_class and "
                "no mapping available"
            )
            raise RiskWeightResolutionError(message)
        if not quality:
            message = (
                f"Exposure {exposure.trade_id} missing quality_step for "
                f"class {exposure_class}"
            )
            raise RiskWeightResolutionError(message)
        quality_path = tuple(
            segment for segment in quality.split("/") if segment
        )
        return (exposure_class, *quality_path)

    def _risk_weight_from_policy(
        self, policy: PolicyData, classification_path: tuple[str, ...]
    ) -> float:
        node: Mapping[str, float | Mapping[str, float]] = policy.risk_weights[
            "exposures"
        ]
        for segment in classification_path:
            if segment not in node:
                message = (
                    "Classification path {path} not present in policy"
                ).format(path="/".join(classification_path))
                raise RiskWeightResolutionError(message)
            next_node = node[segment]
            if isinstance(next_node, Mapping):
                node = next_node  # type: ignore[assignment]
            else:
                node = {segment: next_node}
        last_segment = classification_path[-1]
        value = node.get(last_segment)
        if not isinstance(value, int | float):
            message = (
                "Classification path {path} resolved to non-numeric value"
            ).format(path="/".join(classification_path))
            raise RiskWeightResolutionError(message)
        return float(value)

    def _resolve_lgd(
        self, policy: PolicyData, exposure: models.Exposure
    ) -> float | None:
        if not exposure.lgd_grade and not exposure.exposure_class:
            return None
        lgd_table = policy.lgd_tables.get("lgd", {})
        exposure_key = exposure.exposure_class or ""
        lgd_grade = exposure.lgd_grade
        if exposure_key:
            node = lgd_table.get(exposure_key)
            if isinstance(node, Mapping):
                if lgd_grade and lgd_grade in node:
                    return float(node[lgd_grade])
                # Fall back to quality step path segments if LGD grade missing
                quality_path = (
                    exposure.quality_step.split("/")
                    if exposure.quality_step
                    else []
                )
                for segment in quality_path:
                    if isinstance(node, Mapping) and segment in node:
                        candidate = node[segment]
                        if isinstance(candidate, int | float):
                            return float(candidate)
                        node = candidate  # type: ignore[assignment]
        if lgd_grade and lgd_grade in lgd_table:
            candidate = lgd_table[lgd_grade]
            if isinstance(candidate, int | float):
                return float(candidate)
        return None


__all__ = ["DRCSACalculationEngine", "RiskWeightResolutionError"]
