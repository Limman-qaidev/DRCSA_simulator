"""Reference data router exposing policy tables."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from ...domain.engine import PolicyDataLoader, PolicyDataValidationError
from ..dependencies import get_policy_loader
from ..framework import APIRouter, HTTPException

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/reference", tags=["reference"])


def _load_policy(
    policy_name: str, loader: PolicyDataLoader
) -> Mapping[str, Mapping[str, object]]:
    try:
        policy = loader.load(policy_name)
    except PolicyDataValidationError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "mappings": policy.mappings,
        "hedging_rules": policy.hedging_rules,
        "risk_weights": policy.risk_weights,
        "lgd_tables": policy.lgd_tables,
    }


@router.get("/policies/{policy_name}/mappings")
def policy_mappings(policy_name: str) -> Mapping[str, object]:
    """Return product mappings for a policy."""

    LOGGER.debug("Request for policy mappings of %s", policy_name)
    loader = get_policy_loader()
    return _load_policy(policy_name, loader)["mappings"]


@router.get("/policies/{policy_name}/hedges")
def policy_hedges(policy_name: str) -> Mapping[str, object]:
    """Return hedging rules for a policy."""

    LOGGER.debug("Request for hedging rules of %s", policy_name)
    loader = get_policy_loader()
    return _load_policy(policy_name, loader)["hedging_rules"]


@router.get("/policies/{policy_name}/risk-weights")
def policy_risk_weights(policy_name: str) -> Mapping[str, object]:
    LOGGER.debug("Request for risk weights of %s", policy_name)
    loader = get_policy_loader()
    return _load_policy(policy_name, loader)["risk_weights"]


@router.get("/policies/{policy_name}/lgd")
def policy_lgd(policy_name: str) -> Mapping[str, object]:
    LOGGER.debug("Request for LGD tables of %s", policy_name)
    loader = get_policy_loader()
    return _load_policy(policy_name, loader)["lgd_tables"]
