"""Lightweight HTTP routing primitives for tests without external deps.

The simulator's automated test-suite exercises the HTTP surface without
requiring FastAPI or an ASGI server.  This module therefore exposes a tiny
router abstraction that mimics the subset of FastAPI features the application
needs.  When FastAPI is available the application can be materialised into a
real instance via :meth:`APIApplication.to_fastapi`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from inspect import Signature, signature
from typing import Any

_FastAPIApp: Any
_FastAPIHTTPException: Any
_FastAPIResponse: Any
_fastapi_status: Any

try:  # pragma: no cover - optional dependency import path
    from fastapi import FastAPI as _ImportedFastAPIApp
    from fastapi import HTTPException as _ImportedHTTPException
    from fastapi import status as _imported_status
    from fastapi.responses import JSONResponse as _ImportedJSONResponse
except Exception:  # pragma: no cover - the stdlib-only path is fully tested
    _FastAPIApp = None
    _FastAPIHTTPException = None
    _FastAPIResponse = None
    _fastapi_status = None
else:  # pragma: no cover - executed when FastAPI is available
    _FastAPIApp = _ImportedFastAPIApp
    _FastAPIHTTPException = _ImportedHTTPException
    _FastAPIResponse = _ImportedJSONResponse
    _fastapi_status = _imported_status


class HTTPException(Exception):
    """Exception carrying an HTTP status code and serialisable detail."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass
class Response:
    """Simple response container mirroring FastAPI's minimal interface."""

    status_code: int
    body: Any = None


if _fastapi_status is not None:  # pragma: no branch
    status = _fastapi_status
else:

    class _StatusCodes:
        """Subset of HTTP status codes referenced in the application."""

        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_204_NO_CONTENT = 204
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404

    status = _StatusCodes()


@dataclass
class _Route:
    method: str
    path_template: str
    handler: Callable[..., Any]
    status_code: int


class APIRouter:
    """Collects request handlers with an optional URL prefix."""

    def __init__(
        self, prefix: str = "", tags: Iterable[str] | None = None
    ) -> None:
        self.prefix = prefix.rstrip("/")
        self.tags = tuple(tags or ())
        self._routes: list[_Route] = []

    @property
    def routes(self) -> list[_Route]:
        return list(self._routes)

    def _register(
        self,
        method: str,
        path: str,
        handler: Callable[..., Any],
        status_code: int,
    ) -> Callable[..., Any]:
        template = f"{self.prefix}{path}" or "/"
        self._routes.append(_Route(method, template, handler, status_code))
        return handler

    def get(
        self,
        path: str,
        *,
        response_model: object | None = None,
        status_code: int = status.HTTP_200_OK,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        del response_model

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._register("GET", path, func, status_code)

        return decorator

    def post(
        self,
        path: str,
        *,
        response_model: object | None = None,
        status_code: int = status.HTTP_200_OK,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        del response_model

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._register("POST", path, func, status_code)

        return decorator

    def put(
        self,
        path: str,
        *,
        response_model: object | None = None,
        status_code: int = status.HTTP_200_OK,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        del response_model

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._register("PUT", path, func, status_code)

        return decorator

    def delete(
        self,
        path: str,
        *,
        status_code: int = status.HTTP_200_OK,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return self._register("DELETE", path, func, status_code)

        return decorator


class APIApplication:
    """Minimal application container supporting router style registration."""

    def __init__(self, **metadata: Any) -> None:
        self.metadata = metadata
        self._routes: list[_Route] = []

    def include_router(self, router: APIRouter) -> None:
        self._routes.extend(router.routes)

    def get(
        self,
        path: str,
        *,
        tags: Iterable[str] | None = None,
        status_code: int = status.HTTP_200_OK,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        del tags

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._routes.append(_Route("GET", path or "/", func, status_code))
            return func

        return decorator

    def handle_request(
        self,
        method: str,
        path: str,
        *,
        payload: Any = None,
        query: Mapping[str, Any] | None = None,
    ) -> Response:
        query = dict(query or {})
        for route in self._routes:
            if route.method != method:
                continue
            params = self._match_path(route.path_template, path)
            if params is None:
                continue
            return self._dispatch(
                route, params, payload, query, convert_exceptions=False
            )
        return Response(
            status_code=status.HTTP_404_NOT_FOUND,
            body={"detail": f"No route for {method} {path}"},
        )

    def to_fastapi(self) -> Any:
        """Materialise the stub routes into a FastAPI app when available."""

        if _FastAPIApp is None or _FastAPIResponse is None:
            raise RuntimeError(
                "FastAPI is not installed; cannot create a FastAPI application"
            )

        fastapi_app = _FastAPIApp(**self.metadata)

        for route in self._routes:

            async def endpoint(request: Any, __route: _Route = route) -> Any:
                payload: Any = None
                if request.method in {"POST", "PUT", "PATCH"}:
                    payload = await request.json()
                response = self._dispatch(
                    __route,
                    request.path_params,
                    payload,
                    dict(request.query_params.multi_items()),
                    convert_exceptions=True,
                )
                return _FastAPIResponse(
                    content=response.body, status_code=response.status_code
                )

            fastapi_app.add_api_route(
                route.path_template or "/",
                endpoint,
                methods=[route.method],
                status_code=route.status_code,
            )

        return fastapi_app

    @staticmethod
    def _match_path(template: str, path: str) -> dict[str, str] | None:
        template_parts = [
            part for part in template.strip("/").split("/") if part
        ]
        path_parts = [part for part in path.strip("/").split("/") if part]
        if template_parts != path_parts and "{" not in template:
            if template_parts or path_parts:
                return None
            return {}
        if len(template_parts) != len(path_parts):
            return None
        params: dict[str, str] = {}
        for template_part, value in zip(
            template_parts, path_parts, strict=True
        ):
            if template_part.startswith("{") and template_part.endswith("}"):
                params[template_part[1:-1]] = value
            elif template_part != value:
                return None
        return params

    @staticmethod
    def _invoke(
        handler: Callable[..., Any],
        params: Mapping[str, str],
        payload: Any,
        query: MutableMapping[str, Any],
    ) -> Any:
        sig: Signature = signature(handler)
        kwargs: dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name in params:
                kwargs[name] = params[name]
                continue
            if name in query:
                value = query[name]
                if isinstance(value, str):
                    lowered = value.lower()
                    if lowered in {"true", "false"}:
                        value = lowered == "true"
                kwargs[name] = value
                continue
            if name == "payload":
                kwargs[name] = payload
                continue
            if param.default is not param.empty:
                kwargs[name] = param.default
                continue
            raise TypeError(
                f"Cannot populate parameter '{name}' for handler {handler}"
            )
        return handler(**kwargs)

    def _dispatch(
        self,
        route: _Route,
        params: Mapping[str, Any],
        payload: Any,
        query: MutableMapping[str, Any],
        *,
        convert_exceptions: bool,
    ) -> Response:
        try:
            result = self._invoke(route.handler, params, payload, query)
        except HTTPException as exc:
            if convert_exceptions and _FastAPIHTTPException is not None:
                raise _FastAPIHTTPException(
                    status_code=getattr(exc, "status_code", 500),
                    detail=getattr(exc, "detail", str(exc)),
                ) from exc
            status_code = getattr(
                exc, "status_code", status.HTTP_400_BAD_REQUEST
            )
            detail = getattr(exc, "detail", str(exc))
            return Response(status_code=status_code, body={"detail": detail})
        if isinstance(result, Response):
            return result
        return Response(status_code=route.status_code, body=result)


__all__ = [
    "APIApplication",
    "APIRouter",
    "HTTPException",
    "Response",
    "status",
]
