"""In-memory persistence components."""

from __future__ import annotations

import logging
from collections.abc import Iterable

from ..domain.models import ScenarioDefinition, ScenarioRegistryEntry

LOGGER = logging.getLogger(__name__)


class InMemoryScenarioStore:
    """Simple in-memory scenario registry for the API and UI."""

    def __init__(self) -> None:
        self._storage: dict[str, ScenarioDefinition] = {}

    def list(self) -> Iterable[ScenarioRegistryEntry]:
        for scenario in self._storage.values():
            yield ScenarioRegistryEntry(
                name=scenario.name,
                description=scenario.description,
                created_at=scenario.created_at,
                tags=scenario.tags,
            )

    def get(self, name: str) -> ScenarioDefinition | None:
        return self._storage.get(name)

    def save(self, scenario: ScenarioDefinition) -> None:
        LOGGER.info("Persisting scenario '%s'", scenario.name)
        self._storage[scenario.name] = scenario

    def delete(self, name: str) -> None:
        if name in self._storage:
            LOGGER.info("Deleting scenario '%s'", name)
            del self._storage[name]

    def clear(self) -> None:
        LOGGER.warning("Clearing all scenarios from in-memory store")
        self._storage.clear()
