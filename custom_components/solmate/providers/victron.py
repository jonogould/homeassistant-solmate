"""Victron Energy VRM Cloud REST API provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_SITE_ID, CONF_TOKEN
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_SITE_ID, CONF_TOKEN
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class VictronProvider(BaseSolarProvider):
    """Provider for Victron Energy VRM API."""

    BASE_URL = "https://vrmapi.victronenergy.com"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Victron provider."""
        super().__init__(session, config)
        self.site_id: str = str(config.get(CONF_SITE_ID, "")).strip()
        self.token: str = str(config.get(CONF_TOKEN, "")).strip()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "x-authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

    async def test_connection(self) -> None:
        """Test VRM token and site ID validity."""
        if not self.site_id or not self.token:
            raise SolmateAuthError("Installation ID and VRM Access Token are required.")

        url = f"{self.BASE_URL}/v2/installations/{self.site_id}/diagnostics"

        try:
            async with self.session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Invalid Victron VRM Token or Installation ID (401/403).")
                if resp.status != 200:
                    raise SolmateApiError(f"Victron VRM API error HTTP {resp.status}")
                data = await resp.json()
                if not data.get("success", False) and "records" not in data:
                    raise SolmateApiError("Malformed Victron VRM response.")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot connect to Victron VRM API: {ex}") from ex

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch real-time diagnostics and power flow."""
        url = f"{self.BASE_URL}/v2/installations/{self.site_id}/diagnostics"

        try:
            async with self.session.get(
                url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Invalid Victron VRM Token or Installation ID.")
                if resp.status != 200:
                    raise SolmateApiError(f"Victron API error HTTP {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Connection failed: {ex}") from ex

        records = data.get("records") or []
        soc: float = 0.0
        pv_watts: float = 0.0
        batt_watts: float = 0.0
        grid_watts: float = 0.0
        load_watts: float = 0.0
        daily_pv: float | None = None

        for item in records:
            desc = str(item.get("description") or "").lower()
            val = float(item.get("rawValue") or 0.0)

            if "state of charge" in desc or "soc" in desc:
                soc = val / 100.0
            elif "pv" in desc or "solar yield" in desc or "solar power" in desc:
                pv_watts = max(pv_watts, val)
            elif "battery power" in desc or "dc power" in desc:
                batt_watts = val
            elif "grid power" in desc or "ac input" in desc:
                grid_watts = val
            elif "ac load" in desc or "consumption" in desc:
                load_watts = val
            elif "yield today" in desc or "today energy" in desc:
                daily_pv = val

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc)),
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=round(pv_watts, 1),
            batt_power=round(batt_watts, 1),
            grid_power=round(grid_watts, 1),
            load_power=round(load_watts, 1),
            daily_pv_yield_kwh=round(daily_pv, 2) if daily_pv is not None else None,
        )
