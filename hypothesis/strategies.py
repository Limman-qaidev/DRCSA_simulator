"""Strategies used by the lightweight hypothesis stub."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any


class Strategy:
    def example(self) -> Any:  # pragma: no cover - overridden in subclasses
        raise NotImplementedError


@dataclass(slots=True)
class _SampledFromStrategy(Strategy):
    population: Sequence[Any]

    def example(self) -> Any:
        if not self.population:
            raise ValueError("sampled_from requires a non-empty population")
        return self.population[0]


class _DataProxy:
    def draw(self, strategy: Strategy) -> Any:
        return strategy.example()


class _DataStrategy(Strategy):
    def example(self) -> _DataProxy:
        return _DataProxy()


def data() -> Strategy:
    return _DataStrategy()


def sampled_from(population: Iterable[Any]) -> Strategy:
    return _SampledFromStrategy(tuple(population))


__all__ = ["data", "sampled_from"]
