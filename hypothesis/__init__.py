"""Minimal hypothesis stub supplying the features used in tests."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import Signature, signature
from typing import Any, cast

from . import strategies as st


def given(
    *strategies: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a decorator executing the test once with generated data."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        original_signature = signature(func)
        parameters = list(original_signature.parameters.values())
        strategy_parameters = (
            parameters[-len(strategies) :] if strategies else []
        )
        kept_parameters = (
            parameters[: -len(strategies)] if strategies else parameters
        )

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            generated = [strategy.example() for strategy in strategies]
            for parameter, value in zip(
                strategy_parameters, generated, strict=False
            ):
                kwargs[parameter.name] = value
            return func(*args, **kwargs)

        cast(Any, wrapper).__signature__ = Signature(
            parameters=tuple(kept_parameters),
            return_annotation=original_signature.return_annotation,
        )
        return wrapper

    return decorator


__all__ = ["given", "st"]
