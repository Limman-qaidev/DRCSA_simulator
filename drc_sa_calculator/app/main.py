"""FastAPI entrypoint for the DRCSA calculator services."""

from __future__ import annotations

import logging

from .framework import APIApplication, Response, status
from .routers import compute, datasets, reference, scenarios

LOGGER = logging.getLogger(__name__)


def create_app() -> APIApplication:
    """Instantiate the FastAPI application."""

    application = APIApplication(
        title="DRC SA Calculator",
        version="0.1.0",
        description=(
            "Default Risk Charge (SA) calculation and scenario comparison "
            "service"
        ),
    )
    application.include_router(datasets.router)
    application.include_router(scenarios.router)
    application.include_router(compute.router)
    application.include_router(reference.router)

    @application.get("/health", tags=["system"])
    def health() -> Response:
        return Response(status_code=status.HTTP_200_OK, body={"status": "ok"})

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
