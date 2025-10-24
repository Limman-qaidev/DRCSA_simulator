"""Utility HTTP client for interacting with the FastAPI backend."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import httpx

LOGGER = logging.getLogger(__name__)


class ApiClient:
    """Wrapper around :class:`httpx.AsyncClient` for convenience."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def list_policies(self) -> Sequence[str]:
        LOGGER.debug("Fetching policy list from %s", self._base_url)
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get("/datasets/policies")
            response.raise_for_status()
            return response.json()

    async def get_policy_tables(self, policy_name: str) -> Mapping[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get(f"/datasets/policies/{policy_name}")
            response.raise_for_status()
            return response.json().get("tables", {})

    async def list_scenarios(self) -> Sequence[Mapping[str, Any]]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get("/scenarios")
            response.raise_for_status()
            return response.json()

    async def get_scenario(self, name: str) -> Mapping[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get(f"/scenarios/{name}")
            response.raise_for_status()
            return response.json()

    async def save_scenario(
        self, name: str, payload: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.put(f"/scenarios/{name}", json=payload)
            response.raise_for_status()
            return response.json()

    async def delete_scenario(self, name: str) -> None:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.delete(f"/scenarios/{name}")
            response.raise_for_status()

    async def compute(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        LOGGER.debug("Submitting computation request to %s", self._base_url)
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.post("/compute", json=payload)
            response.raise_for_status()
            return response.json()

    async def compute_matrix(
        self,
        policy: str,
        baseline: Mapping[str, Any],
        scenarios: Iterable[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        return await self.compute(
            {
                "policy": policy,
                "baseline": baseline,
                "scenarios": list(scenarios),
            }
        )
