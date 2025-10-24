"""Datasets router exposing policy metadata."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ...domain.engine import PolicyDataLoader, PolicyDataValidationError
from .. import schemas
from ..dependencies import get_policy_loader

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/policies", response_model=list[str])
def list_policies(
    loader: Annotated[PolicyDataLoader, Depends(get_policy_loader)],
) -> list[str]:
    """Return the list of available regulatory policies."""

    policies = list(loader.available_policies())
    LOGGER.debug("Returning %s policies", len(policies))
    return policies


@router.get(
    "/policies/{policy_name}", response_model=schemas.PolicySummaryModel
)
def get_policy(
    policy_name: str,
    loader: Annotated[PolicyDataLoader, Depends(get_policy_loader)],
) -> schemas.PolicySummaryModel:
    """Return metadata for a specific policy."""

    try:
        policy = loader.load(policy_name)
    except PolicyDataValidationError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return schemas.PolicySummaryModel(name=policy.name, tables=policy.hashes)
