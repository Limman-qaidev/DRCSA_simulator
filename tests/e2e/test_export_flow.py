from __future__ import annotations

import socket
import threading
import time
from typing import Any, Dict, TYPE_CHECKING

import pytest

_playwright = pytest.importorskip("playwright.sync_api")

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from playwright.sync_api import APIResponse, APIRequestContext
else:  # pragma: no cover - runtime alias when Playwright is available
    APIResponse = Any
    APIRequestContext = Any

import uvicorn

from drc_sa_calculator.app.dependencies import get_scenario_store
from drc_sa_calculator.app.main import create_app

pytestmark = pytest.mark.e2e


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        _, port = sock.getsockname()
        return int(port)


def _wait_for_port(port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(("127.0.0.1", port))
                return
            except OSError:
                time.sleep(0.05)
    raise TimeoutError(f"Server on port {port} did not start within {timeout} seconds")


@pytest.fixture(scope="module")
def api_server() -> str:
    app = create_app()
    port = _reserve_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="uvicorn-test-server", daemon=True)
    thread.start()
    _wait_for_port(port)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def _serialise_scenario(scenario) -> Dict[str, Any]:
    return {
        "name": scenario.name,
        "description": scenario.description,
        "tags": list(scenario.tags),
        "exposures": [
            {
                "trade_id": exposure.trade_id,
                "notional": exposure.notional,
                "currency": exposure.currency,
                "product_type": exposure.product_type,
                "exposure_class": exposure.exposure_class,
                "quality_step": exposure.quality_step,
                "counterparty_grade": exposure.counterparty_grade,
                "lgd_grade": exposure.lgd_grade,
                "hedging_set": exposure.hedging_set,
                "metadata": dict(exposure.metadata),
            }
            for exposure in scenario.exposures
        ],
    }


def _ensure_ok(response: APIResponse) -> Dict[str, Any]:
    assert response.ok, response.text()
    return response.json()


def test_export_flow_via_rest(api_server, baseline_scenario, stress_scenario) -> None:
    get_scenario_store().clear()
    with _playwright.sync_playwright() as pw:
        request_context: APIRequestContext = pw.request.new_context(base_url=api_server)
        try:
            for scenario in (baseline_scenario, stress_scenario):
                payload = _serialise_scenario(scenario)
                response = request_context.put(f"/scenarios/{scenario.name}", json=payload)
                stored = _ensure_ok(response)
                assert stored["name"] == scenario.name

            baseline_payload = _ensure_ok(
                request_context.get(f"/scenarios/{baseline_scenario.name}")
            )
            stress_payload = _ensure_ok(request_context.get(f"/scenarios/{stress_scenario.name}"))

            compute_response = _ensure_ok(
                request_context.post(
                    "/compute",
                    json={
                        "policy": "BCBS_MAR",
                        "baseline": baseline_payload,
                        "scenarios": [stress_payload],
                    },
                )
            )

            baseline_total = compute_response["result"]["baseline"]["total_capital_charge"]
            stress_total = compute_response["result"]["scenarios"][0]["total_capital_charge"]
            delta = compute_response["comparisons"][0]["delta_total_charge"]

            assert baseline_total == pytest.approx(261_250.0)
            assert stress_total == pytest.approx(305_000.0)
            assert delta == pytest.approx(stress_total - baseline_total)

            policy_hashes = compute_response["result"]["policy"]["hashes"]
            assert {"risk_weights", "lgd_tables", "mappings", "hedging_rules", "policy"}.issubset(
                policy_hashes
            )
        finally:
            request_context.dispose()
