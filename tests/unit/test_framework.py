"""Unit tests for the lightweight HTTP framework shim."""

from __future__ import annotations

import pytest

from drc_sa_calculator.app import framework
from drc_sa_calculator.app.framework import (
    APIApplication,
    APIRouter,
    HTTPException,
    Response,
    status,
)


def test_handle_request_dispatches_router_handler() -> None:
    """Application should execute registered handlers via handle_request."""

    app = APIApplication()
    router = APIRouter(prefix="/ping")

    @router.get("")
    def ping() -> dict[str, str]:
        return {"message": "pong"}

    app.include_router(router)

    response = app.handle_request("GET", "/ping")

    assert response.status_code == status.HTTP_200_OK
    assert response.body == {"message": "pong"}


def test_handle_request_converts_http_exception() -> None:
    """HTTPException raised in handlers should be serialised to a response."""

    app = APIApplication()
    router = APIRouter(prefix="/errors")

    @router.get("")
    def boom() -> Response:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "boom")

    app.include_router(router)

    response = app.handle_request("GET", "/errors")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.body == {"detail": "boom"}


def test_to_fastapi_conversion_path() -> None:
    """FastAPI conversion raises when unavailable and succeeds otherwise."""

    app = APIApplication()
    router = APIRouter(prefix="/ping")

    @router.get("")
    def ping() -> dict[str, str]:
        return {"ok": "true"}

    app.include_router(router)

    fastapi_cls = getattr(framework, "_FastAPIApp", None)

    if fastapi_cls is None:
        with pytest.raises(RuntimeError, match="FastAPI is not installed"):
            app.to_fastapi()
    else:
        fastapi_app = app.to_fastapi()
        paths = {route.path for route in fastapi_app.routes}
        assert "/ping" in paths
