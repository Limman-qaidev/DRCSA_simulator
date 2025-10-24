"""Validation rules for DRCSA scenarios and data."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from .models import Exposure, ScenarioDefinition

LOGGER = logging.getLogger(__name__)


class ScenarioValidationError(ValueError):
    """Raised when scenario validation fails."""


def _ensure_positive_notional(exposure: Exposure) -> None:
    if exposure.notional <= 0:
        raise ScenarioValidationError(
            f"Exposure {exposure.trade_id} must have positive notional"
        )


def _ensure_currency(exposure: Exposure) -> None:
    if not exposure.currency:
        raise ScenarioValidationError(
            f"Exposure {exposure.trade_id} requires a reporting currency"
        )


def validate_scenario(scenario: ScenarioDefinition) -> None:
    """Validate that a scenario definition is well formed."""

    LOGGER.debug(
        "Validating scenario '%s' with %s exposures",
        scenario.name,
        len(scenario.exposures),
    )
    if not scenario.exposures:
        raise ScenarioValidationError(
            f"Scenario '{scenario.name}' must contain at least one exposure"
        )
    seen: set[str] = set()
    for exposure in scenario.exposures:
        _ensure_positive_notional(exposure)
        _ensure_currency(exposure)
        if exposure.trade_id in seen:
            message = (
                f"Scenario '{scenario.name}' contains duplicate trade id "
                f"'{exposure.trade_id}'"
            )
            raise ScenarioValidationError(message)
        seen.add(exposure.trade_id)


def validate_scenarios(scenarios: Iterable[ScenarioDefinition]) -> None:
    """Validate multiple scenarios."""

    for scenario in scenarios:
        validate_scenario(scenario)
