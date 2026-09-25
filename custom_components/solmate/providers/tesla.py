"""Tesla Powerwall Local Gateway provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_GATEWAY_IP, CONF_PASSWORD
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_GATEWAY_IP, CONF_PASSWORD
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class TeslaProvider(BaseSolarProvider):
    """Provider for Tesla Powerwall local gateway."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Tesla Powerwall provider."""
        super().__init__(session, config)
        host = str(config.get(CONF_GATEWAY_IP, "")).strip()
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"https://{host}"
        self.base_url = host.rstrip("/")
        self.password: str = str(config.get(CONF_PASSWORD, "")).strip()

    async def test_connection(self) -> None:
        """Test reachability of local Powerwall gateway."""
        if not self.base_url or self.base_url in ("http://", "https://"):
            raise SolmateAuthError("Powerwall Gateway IP / Host is required.")

        url = f"{self.base_url}/api/system_status/soe"
        try:
            async with self.session.get(
                url, ssl=False, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status not in (200, 401, 403):
                    raise SolmateApiError(f"Powerwall gateway error HTTP {resp.status}")
                if resp.status in (401, 403):
                    # Check if meters is open without auth
                    meter_url = f"{self.base_url}/api/meters/aggregates"
                    async with self.session.get(
                        meter_url, ssl=False, timeout=aiohttp.ClientTimeout(total=10)
                    ) as m_resp:
                        if m_resp.status != 200:
                            raise SolmateAuthError("Authentication required on Powerwall gateway.")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot reach Tesla Powerwall gateway: {ex}") from ex

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch battery percentage and meter aggregates."""
        soc: float = 0.0
        pv_watts: float = 0.0
        batt_watts: float = 0.0
        grid_watts: float = 0.0
        load_watts: float = 0.0

        # 1. State of Energy (SOE)
        try:
            soe_url = f"{self.base_url}/api/system_status/soe"
            async with self.session.get(
                soe_url, ssl=False, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pct = data.get("percentage")
                    if pct is not None:
                        soc = float(pct) / 100.0
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.debug("Tesla SOE fetch skipped/failed: %s", ex)

        # 2. Power Meters
        try:
            meter_url = f"{self.base_url}/api/meters/aggregates"
            async with self.session.get(
                meter_url, ssl=False, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    solar = data.get("solar") or {}
                    battery = data.get("battery") or {}
                    site = data.get("site") or {}
                    load = data.get("load") or {}

                    pv_watts = max(0.0, float(solar.get("instant_power") or 0.0))
                    # In Tesla Powerwall meters, positive = discharging, negative = charging
                    batt_watts = float(battery.get("instant_power") or 0.0)
                    grid_watts = float(site.get("instant_power") or 0.0)
                    load_watts = max(0.0, float(load.get("instant_power") or 0.0))
                else:
                    raise SolmateApiError(f"Tesla meters error HTTP {resp.status}")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Powerwall meter connection failed: {ex}") from ex

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc)),
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=round(pv_watts, 1),
            batt_power=round(batt_watts, 1),
            grid_power=round(grid_watts, 1),
            load_power=round(load_watts, 1),
        )
