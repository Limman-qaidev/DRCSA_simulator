"""Scenario router for CRUD style operations."""

from __future__ import annotations

import logging

from ...domain.rules import validate_scenario
from .. import schemas
from ..dependencies import get_scenario_store
from ..framework import APIRouter, HTTPException, Response, status

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[schemas.ScenarioSummaryModel])
def list_scenarios() -> list[dict[str, object]]:
    """Return the registered scenarios."""

    store = get_scenario_store()
    summaries = [
        schemas.ScenarioSummaryModel.from_domain(item).to_dict()
        for item in store.list()
    ]
    LOGGER.debug("Returning %s scenarios", len(summaries))
    return summaries


@router.get("/{name}", response_model=schemas.ScenarioModel)
def get_scenario(name: str) -> dict[str, object]:
    store = get_scenario_store()
    scenario = store.get(name)
    if not scenario:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{name}' not found"
        )
    return schemas.ScenarioModel.from_domain(scenario).to_dict()


@router.put(
    "/{name}",
    response_model=schemas.ScenarioModel,
    status_code=status.HTTP_201_CREATED,
)
def upsert_scenario(
    name: str,
    payload: dict[str, object],
) -> dict[str, object]:
    store = get_scenario_store()
    model = schemas.ScenarioModel.from_dict(payload)
    scenario = model.to_domain()
    validate_scenario(scenario)
    if scenario.name != name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scenario name in path and payload must match",
        )
    store.save(scenario)
    LOGGER.info("Scenario '%s' persisted", name)
    return schemas.ScenarioModel.from_domain(scenario).to_dict()


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(name: str) -> Response:
    store = get_scenario_store()
    if not store.get(name):
        raise HTTPException(
            status_code=404, detail=f"Scenario '{name}' not found"
        )
    store.delete(name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
