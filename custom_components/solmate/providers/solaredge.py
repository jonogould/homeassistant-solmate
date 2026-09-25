"""SolarEdge Monitoring API provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_API_KEY, CONF_SITE_ID
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_API_KEY, CONF_SITE_ID
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class SolarEdgeProvider(BaseSolarProvider):
    """Provider for SolarEdge monitoring API."""

    BASE_URL = "https://monitoringapi.solaredge.com"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize SolarEdge provider."""
        super().__init__(session, config)
        self.site_id: str = str(config.get(CONF_SITE_ID, "")).strip()
        self.api_key: str = str(config.get(CONF_API_KEY, "")).strip()

    async def test_connection(self) -> None:
        """Test API key and Site ID validity."""
        if not self.site_id or not self.api_key:
            raise SolmateAuthError("Site ID and API Key are required.")

        url = f"{self.BASE_URL}/site/{self.site_id}/currentPowerFlow"
        params = {"api_key": self.api_key}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Invalid SolarEdge API Key or Site ID (401/403).")
                if resp.status != 200:
                    raise SolmateApiError(f"SolarEdge API error HTTP {resp.status}")
                data = await resp.json()
                if "siteCurrentPowerFlow" not in data:
                    raise SolmateApiError("Malformed SolarEdge response.")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot connect to SolarEdge API: {ex}") from ex

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch current power flow telemetry."""
        url = f"{self.BASE_URL}/site/{self.site_id}/currentPowerFlow"
        params = {"api_key": self.api_key}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Invalid SolarEdge API Key or Site ID.")
                if resp.status != 200:
                    raise SolmateApiError(f"SolarEdge API error HTTP {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Connection failed: {ex}") from ex

        flow = data.get("siteCurrentPowerFlow", {})
        unit = str(flow.get("unit", "")).lower()
        multiplier = 1000.0 if unit == "kw" else 1.0

        pv_node = flow.get("PV") or {}
        load_node = flow.get("LOAD") or {}
        grid_node = flow.get("GRID") or {}
        storage_node = flow.get("STORAGE") or {}

        pv_watts = float(pv_node.get("currentPower") or 0.0) * multiplier
        load_watts = float(load_node.get("currentPower") or 0.0) * multiplier
        grid_watts = float(grid_node.get("currentPower") or 0.0) * multiplier

        raw_batt = float(storage_node.get("currentPower") or 0.0) * multiplier
        batt_status = str(storage_node.get("status") or "").lower()

        if "charg" in batt_status and "discharg" not in batt_status:
            batt_watts = -abs(raw_batt)
        elif "discharg" in batt_status:
            batt_watts = abs(raw_batt)
        else:
            batt_watts = 0.0

        soc = float(storage_node.get("chargeLevel") or 0.0) / 100.0

        # Try to fetch overview for daily PV yield
        daily_pv: float | None = None
        try:
            overview_url = f"{self.BASE_URL}/site/{self.site_id}/overview"
            async with self.session.get(overview_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as ov_resp:
                if ov_resp.status == 200:
                    ov_data = await ov_resp.json()
                    last_day_energy = ov_data.get("overview", {}).get("lastDayData", {}).get("energy")
                    if last_day_energy is not None:
                        daily_pv = float(last_day_energy) / 1000.0
        except Exception:  # pylint: disable=broad-except
            pass

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
