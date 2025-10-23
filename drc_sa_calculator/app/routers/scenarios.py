"""Scenario router for CRUD style operations."""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from .. import schemas
from ..dependencies import get_scenario_store
from ...domain.models import ScenarioDefinition
from ...domain.rules import validate_scenario
from ...infrastructure.memory import InMemoryScenarioStore

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=List[schemas.ScenarioSummaryModel])
def list_scenarios(store: InMemoryScenarioStore = Depends(get_scenario_store)) -> List[schemas.ScenarioSummaryModel]:
    """Return the registered scenarios."""

    summaries = [
        schemas.ScenarioSummaryModel(
            name=item.name,
            description=item.description,
            created_at=item.created_at,
            tags=item.tags,
        )
        for item in store.list()
    ]
    LOGGER.debug("Returning %s scenarios", len(summaries))
    return summaries


@router.get("/{name}", response_model=schemas.ScenarioModel)
def get_scenario(name: str, store: InMemoryScenarioStore = Depends(get_scenario_store)) -> schemas.ScenarioModel:
    scenario = store.get(name)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    return _to_schema(scenario)


@router.put("/{name}", response_model=schemas.ScenarioModel, status_code=status.HTTP_201_CREATED)
def upsert_scenario(
    name: str,
    payload: schemas.ScenarioModel,
    store: InMemoryScenarioStore = Depends(get_scenario_store),
) -> schemas.ScenarioModel:
    scenario = payload.to_domain()
    validate_scenario(scenario)
    if scenario.name != name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scenario name in path and payload must match",
        )
    store.save(scenario)
    LOGGER.info("Scenario '%s' persisted", name)
    return _to_schema(scenario)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(name: str, store: InMemoryScenarioStore = Depends(get_scenario_store)) -> Response:
    if not store.get(name):
        raise HTTPException(status_code=404, detail=f"Scenario '{name}' not found")
    store.delete(name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _to_schema(scenario: ScenarioDefinition) -> schemas.ScenarioModel:
    return schemas.ScenarioModel(
        name=scenario.name,
        description=scenario.description,
        tags=scenario.tags,
        exposures=[
            schemas.ExposureModel(
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
            for exposure in scenario.exposures
        ],
        created_at=scenario.created_at,
    )
