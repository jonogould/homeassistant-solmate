"""Base class and common models for Solmate inverter providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any

import aiohttp

try:
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
        SolmateError,
    )
except (ImportError, ValueError):
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
        SolmateError,
    )

_LOGGER = logging.getLogger(__name__)


class BaseSolarProvider(ABC):
    """Abstract base class for all solar inverter telemetry providers."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize provider with an aiohttp session and configuration dict."""
        self.session = session
        self.config = config

    @abstractmethod
    async def test_connection(self) -> None:
        """Validate credentials / connectivity. Raise exception if failed."""

    @abstractmethod
    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch and return normalized real-time telemetry."""

    async def close(self) -> None:
        """Perform any provider-specific teardown or cleanup."""
