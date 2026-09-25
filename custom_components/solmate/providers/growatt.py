"""Growatt ShineServer API provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import re
from typing import Any

import aiohttp

try:
    from ..const import CONF_PASSWORD, CONF_USERNAME
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_PASSWORD, CONF_USERNAME
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class GrowattProvider(BaseSolarProvider):
    """Provider for Growatt ShineServer API."""

    BASE_URL = "https://server.growatt.com"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Growatt provider."""
        super().__init__(session, config)
        self.username: str = str(config.get(CONF_USERNAME, "")).strip()
        self.password: str = str(config.get(CONF_PASSWORD, "")).strip()
        self._logged_in: bool = False

    async def _login(self) -> None:
        """Log in to Growatt ShineServer."""
        if not self.username or not self.password:
            raise SolmateAuthError("Growatt Username and Password are required.")

        url = f"{self.BASE_URL}/login"
        data = {"account": self.username, "password": self.password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            async with self.session.post(
                url, data=data, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise SolmateAuthError(f"Growatt login failed HTTP {resp.status}")
                text = await resp.text()
                if "error" in text.lower() and "success" not in text.lower():
                    raise SolmateAuthError("Invalid Growatt username or password.")
                self._logged_in = True
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot connect to Growatt server: {ex}") from ex

    async def test_connection(self) -> None:
        """Test credentials by logging in."""
        await self._login()

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch plant energy flow data."""
        if not self._logged_in:
            await self._login()

        url = f"{self.BASE_URL}/index/getPlantListTitle"

        try:
            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise SolmateApiError(f"Growatt plant list error HTTP {resp.status}")
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Growatt connection failed: {ex}") from ex

        total_data = data.get("totalData") or []
        first_plant = total_data[0] if total_data else {}

        pv_watts: float = 0.0
        pwr_str = str(first_plant.get("currentPower") or "")
        match = re.search(r"([\d\.]+)", pwr_str)
        if match:
            raw_pwr = float(match.group(1))
            pv_watts = raw_pwr * 1000.0 if "kw" in pwr_str.lower() else raw_pwr

        daily_pv: float | None = None
        energy_str = str(first_plant.get("todayEnergy") or "")
        e_match = re.search(r"([\d\.]+)", energy_str)
        if e_match:
            daily_pv = float(e_match.group(1))

        soc: float = 0.5  # Growatt plant title does not include battery SOC by default

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc)),
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=round(pv_watts, 1),
            batt_power=0.0,
            grid_power=0.0,
            load_power=round(pv_watts, 1),
            daily_pv_yield_kwh=round(daily_pv, 2) if daily_pv is not None else None,
        )
