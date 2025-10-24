"""Very small subset of schemathesis for offline contract tests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class CaseResponse:
    """Container matching the minimal API used in contract tests."""

    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def json(self) -> Any:
        return self._payload

    def text(self) -> str:
        return json.dumps(self._payload, default=str)


@dataclass(slots=True)
class _Route:
    method: str
    path: str
    status_code: int


class SchemaCase:
    """Represents a single request invocation."""

    def __init__(
        self,
        app: Any,
        route: _Route,
        *,
        body: Mapping[str, Any] | None = None,
    ) -> None:
        self._app = app
        self._route = route
        self._body = body

    def call_asgi(self) -> CaseResponse:
        response = self._app.handle_request(
            self._route.method,
            self._route.path,
            payload=self._body,
        )
        return CaseResponse(response.status_code, response.body)

    def validate_response(self, response: CaseResponse) -> None:
        if not response.ok:
            raise AssertionError(
                "Expected successful response, received "
                f"{response.status_code}"
            )


class _MethodCollection:
    def __init__(self, app: Any, routes: dict[str, _Route]) -> None:
        self._app = app
        self._routes = routes

    def __getitem__(self, method: str) -> _CaseFactory:
        route = self._routes[method.lower()]
        return _CaseFactory(self._app, route)


class _CaseFactory:
    def __init__(self, app: Any, route: _Route) -> None:
        self._app = app
        self._route = route

    def make_case(
        self,
        *,
        body: Mapping[str, Any] | None = None,
        media_type: str | None = None,
        path_parameters: Mapping[str, str] | None = None,
    ) -> SchemaCase:
        del media_type
        if path_parameters:
            path = self._route.path
            for key, value in path_parameters.items():
                path = path.replace(f"{{{key}}}", value)
            route = _Route(self._route.method, path, self._route.status_code)
        else:
            route = self._route
        return SchemaCase(self._app, route, body=body)


class Schema:
    def __init__(self, app: Any) -> None:
        self._app = app
        self._routes: dict[str, dict[str, _Route]] = {}
        for route in getattr(app, "_routes", []):
            path_routes = self._routes.setdefault(route.path_template, {})
            path_routes[route.method.lower()] = _Route(
                route.method, route.path_template, route.status_code
            )

    def __getitem__(self, path: str) -> _MethodCollection:
        return _MethodCollection(self._app, self._routes[path])


def from_asgi(_: str, *, app: Any) -> Schema:
    """Return a simple schema wrapper for the provided application."""

    return Schema(app)


__all__ = ["from_asgi"]
