"""FastAPI entrypoint for the DRCSA calculator services."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .routers import compute, datasets, reference, scenarios

LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Instantiate the FastAPI application."""

    application = FastAPI(
        title="DRC SA Calculator",
        version="0.1.0",
        description=(
            "Default Risk Charge (SA) calculation and scenario comparison "
            "service"
        ),
        openapi_version="3.1.0",
    )
    application.include_router(datasets.router)
    application.include_router(scenarios.router)
    application.include_router(compute.router)
    application.include_router(reference.router)

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    LOGGER.info(
        "FastAPI application created with routers: %s",
        [
            "datasets",
            "scenarios",
            "compute",
            "reference",
        ],
    )
    return application


app = create_app()
