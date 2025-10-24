"""Datasets router exposing policy metadata."""

from __future__ import annotations

import logging

from ...domain.engine import PolicyDataValidationError
from .. import schemas
from ..dependencies import get_policy_loader
from ..framework import APIRouter, HTTPException

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/policies", response_model=list[str])
def list_policies() -> list[str]:
    """Return the list of available regulatory policies."""

    loader = get_policy_loader()
    policies = list(loader.available_policies())
    LOGGER.debug("Returning %s policies", len(policies))
    return policies


@router.get(
    "/policies/{policy_name}", response_model=schemas.PolicySummaryModel
)
def get_policy(
    policy_name: str,
) -> dict[str, object]:
    """Return metadata for a specific policy."""

    loader = get_policy_loader()
    try:
        policy = loader.load(policy_name)
    except PolicyDataValidationError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    summary = schemas.PolicySummaryModel(
        name=policy.name, tables=policy.hashes
    )
    return summary.to_dict()
