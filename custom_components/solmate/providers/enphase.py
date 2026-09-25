"""Enphase Enlighten & Local Envoy provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_GATEWAY_IP, CONF_TOKEN
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_GATEWAY_IP, CONF_TOKEN
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class EnphaseProvider(BaseSolarProvider):
    """Provider for Enphase Envoy local gateway."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Enphase provider."""
        super().__init__(session, config)
        host = str(config.get(CONF_GATEWAY_IP, "")).strip()
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"https://{host}"
        self.base_url = host.rstrip("/")
        self.token: str = str(config.get(CONF_TOKEN, "")).strip()

    @property
    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def test_connection(self) -> None:
        """Test reachability of Envoy gateway."""
        if not self.base_url or self.base_url in ("http://", "https://"):
            raise SolmateAuthError("Envoy Gateway IP / Host is required.")

        url = f"{self.base_url}/ivp/livedata/status"
        try:
            async with self.session.get(
                url,
                headers=self._headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Authentication required. Please provide Envoy Token.")
                if resp.status != 200:
                    # Test fallback
                    fb_url = f"{self.base_url}/api/v1/production"
                    async with self.session.get(
                        fb_url,
                        headers=self._headers,
                        ssl=False,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as fb_resp:
                        if fb_resp.status != 200:
                            raise SolmateApiError(f"Envoy error HTTP {resp.status}")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot reach Envoy gateway: {ex}") from ex

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch live telemetry from Envoy."""
        soc: float = 0.0
        pv_watts: float = 0.0
        batt_watts: float = 0.0
        load_watts: float = 0.0
        grid_watts: float = 0.0

        # Try /ivp/livedata/status
        live_url = f"{self.base_url}/ivp/livedata/status"
        livedata_success = False

        try:
            async with self.session.get(
                live_url,
                headers=self._headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    meters = data.get("meters") or {}
                    soc_raw = data.get("soc") if data.get("soc") is not None else meters.get("storage", {}).get("soc")
                    if soc_raw is not None:
                        soc = float(soc_raw) / 100.0

                    solar = meters.get("solar") or {}
                    storage = meters.get("storage") or {}
                    load = meters.get("load") or {}
                    grid = meters.get("grid") or {}

                    raw_solar = solar.get("agg_p_w")
                    if raw_solar is None and solar.get("agg_p_mw") is not None:
                        raw_solar = float(solar["agg_p_mw"]) / 1000.0
                    pv_watts = max(0.0, float(raw_solar or 0.0))

                    batt_watts = float(storage.get("agg_p_w") or 0.0)
                    load_watts = max(0.0, float(load.get("agg_p_w") or 0.0))
                    grid_watts = float(grid.get("agg_p_w") or 0.0)
                    livedata_success = True
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.debug("Envoy /ivp/livedata/status failed: %s", ex)

        if not livedata_success:
            # Fallback to /api/v1/production
            try:
                prod_url = f"{self.base_url}/api/v1/production"
                async with self.session.get(
                    prod_url,
                    headers=self._headers,
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        pv_watts = float(data.get("wattsNow") or 0.0)
            except Exception as ex:  # pylint: disable=broad-except
                raise SolmateConnectionError(f"Failed to query Envoy endpoints: {ex}") from ex

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc)),
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=round(pv_watts, 1),
            batt_power=round(batt_watts, 1),
            grid_power=round(grid_watts, 1),
            load_power=round(load_watts, 1),
        )
