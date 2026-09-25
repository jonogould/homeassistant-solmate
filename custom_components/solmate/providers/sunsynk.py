"""Sunsynk / Deye Cloud provider for Solmate."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_EMAIL, CONF_GATEWAY_URL, CONF_PASSWORD, DEFAULT_GATEWAY_URL
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
        SunsynkApiClient,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_EMAIL, CONF_GATEWAY_URL, CONF_PASSWORD, DEFAULT_GATEWAY_URL
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
        SunsynkApiClient,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class SunsynkProvider(BaseSolarProvider):
    """Provider for Sunsynk & Deye Cloud inverters."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Sunsynk provider."""
        super().__init__(session, config)
        self.email: str = config.get(CONF_EMAIL, "").strip()
        self.password: str = config.get(CONF_PASSWORD, "")
        gateway_url: str = config.get(CONF_GATEWAY_URL, DEFAULT_GATEWAY_URL)
        self.client = SunsynkApiClient(session=session, base_url=gateway_url)

    async def test_connection(self) -> None:
        """Test credentials by logging in."""
        if not self.email or not self.password:
            raise SolmateAuthError("Email and password are required")
        await self.client.login(self.email, self.password)

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch telemetry with automatic re-authentication if token expired."""
        if not self.client.access_token:
            await self.client.login(self.email, self.password)

        try:
            return await self.client.get_realtime_flow()
        except SolmateAuthError:
            _LOGGER.info("Sunsynk access token expired, re-authenticating...")
            await self.client.login(self.email, self.password)
            return await self.client.get_realtime_flow()

    async def close(self) -> None:
        """Close API client session if owned."""
        await self.client.close()
