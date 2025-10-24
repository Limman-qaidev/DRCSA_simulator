"""Small stub of uvicorn sufficient for the tests in this project."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Config:
    app: Any
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"


class Server:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.should_exit = False

    def run(self) -> None:  # pragma: no cover - stub runtime loop
        while not self.should_exit:
            time.sleep(0.05)


__all__ = ["Config", "Server"]
