"""Computation router for running DRCSA calculations."""

from __future__ import annotations

import logging

from .. import schemas
from ..dependencies import build_comparisons, get_engine
from ..framework import APIRouter

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/compute", tags=["compute"])


@router.post("", response_model=schemas.ComputationResponseModel)
def compute(
    payload: dict[str, object],
    include_comparisons: bool = True,
) -> dict[str, object]:
    """Execute the DRCSA calculator for provided scenarios."""

    request = schemas.ComputationRequestModel.from_dict(payload).to_domain()
    LOGGER.info(
        "Received computation request for policy %s with %s alternative "
        "scenarios",
        request.policy.name,
        len(request.scenarios),
    )
    engine = get_engine()
    result = engine.compute(request)
    comparisons = (
        list(build_comparisons(result.baseline, result.scenarios))
        if include_comparisons
        else []
    )
    response = schemas.ComputationResponseModel.from_domain(
        result, comparisons
    )
    return response.to_dict()
