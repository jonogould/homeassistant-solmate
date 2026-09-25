"""Solarman Smart & Business Open API provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_APP_ID, CONF_APP_SECRET, CONF_STATION_ID
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_APP_ID, CONF_APP_SECRET, CONF_STATION_ID
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class SolarmanProvider(BaseSolarProvider):
    """Provider for Solarman Open API."""

    BASE_URL = "https://globalapi.solarmanpv.com"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Solarman provider."""
        super().__init__(session, config)
        self.app_id: str = str(config.get(CONF_APP_ID, "")).strip()
        self.app_secret: str = str(config.get(CONF_APP_SECRET, "")).strip()
        self.station_id: str = str(config.get(CONF_STATION_ID, "")).strip()
        self._access_token: str | None = None

    async def _get_token(self) -> str:
        """Acquire Solarman access token."""
        if not self.app_id or not self.app_secret or not self.station_id:
            raise SolmateAuthError("Solarman App ID, App Secret, and Station ID are required.")

        url = f"{self.BASE_URL}/account/v1/api/token"
        payload = {"appId": self.app_id, "appSecret": self.app_secret}
        headers = {"Content-Type": "application/json"}

        try:
            async with self.session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise SolmateAuthError(f"Solarman token request failed HTTP {resp.status}")
                data = await resp.json()
                token = data.get("access_token")
                if not token or not data.get("success", False):
                    msg = data.get("msg") or "Invalid Solarman App ID or App Secret."
                    raise SolmateAuthError(msg)
                self._access_token = token
                return token
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot connect to Solarman API: {ex}") from ex

    async def test_connection(self) -> None:
        """Test API token retrieval and station query."""
        token = await self._get_token()
        url = f"{self.BASE_URL}/station/v1/api/realTime"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        try:
            station_int = int(self.station_id)
        except ValueError:
            raise SolmateAuthError("Station ID must be a numeric identifier.")

        payload = {"stationId": station_int}
        try:
            async with self.session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise SolmateApiError(f"Solarman station query failed HTTP {resp.status}")
                data = await resp.json()
                if not data.get("success", False):
                    raise SolmateAuthError(data.get("msg") or "Failed to query Solarman station.")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Solarman connection error: {ex}") from ex

    async def get_energy_flow(self) -> EnergyFlowData:
        """Query real-time station flow."""
        if not self._access_token:
            await self._get_token()

        url = f"{self.BASE_URL}/station/v1/api/realTime"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        payload = {"stationId": int(self.station_id)}

        try:
            async with self.session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status in (401, 403):
                    # Refresh token once
                    await self._get_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self.session.post(
                        url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                    ) as retry_resp:
                        data = await retry_resp.json()
                else:
                    data = await resp.json()
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Solarman query failed: {ex}") from ex

        rt = data.get("data") or {}
        pv_watts = float(rt.get("generationPower") or 0.0)
        batt_watts = float(rt.get("batteryPower") or 0.0)
        soc = float(rt.get("batterySoc") or 0.0) / 100.0
        load_watts = float(rt.get("usePower") or 0.0)
        grid_watts = float(rt.get("gridPower") or 0.0)

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc)),
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=round(pv_watts, 1),
            batt_power=round(batt_watts, 1),
            grid_power=round(grid_watts, 1),
            load_power=round(load_watts, 1),
        )
