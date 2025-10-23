"""Computation router for running DRCSA calculations."""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Query

from .. import schemas
from ..dependencies import build_comparisons, get_engine
from ...domain.engine import DRCSACalculationEngine

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/compute", tags=["compute"])


@router.post("", response_model=schemas.ComputationResponseModel)
def compute(  # noqa: D401 - FastAPI signature
    payload: schemas.ComputationRequestModel,
    engine: DRCSACalculationEngine = Depends(get_engine),
    include_comparisons: bool = Query(default=True, description="Return scenario comparisons"),
) -> schemas.ComputationResponseModel:
    """Execute the DRCSA calculator for provided scenarios."""

    request = payload.to_domain()
    LOGGER.info(
        "Received computation request for policy %s with %s alternative scenarios",
        request.policy.name,
        len(request.scenarios),
    )
    result = engine.compute(request)
    comparisons = build_comparisons(result.baseline, result.scenarios) if include_comparisons else []
    return schemas.ComputationResponseModel.from_domain(result, comparisons)
