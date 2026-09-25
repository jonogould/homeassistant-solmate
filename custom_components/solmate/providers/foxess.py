"""FoxESS Cloud Open API provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_API_KEY, CONF_DEVICE_SN
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_API_KEY, CONF_DEVICE_SN
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class FoxEssProvider(BaseSolarProvider):
    """Provider for FoxESS Cloud Open API."""

    BASE_URL = "https://www.foxesscloud.com"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize FoxESS provider."""
        super().__init__(session, config)
        self.device_sn: str = str(config.get(CONF_DEVICE_SN, "")).strip()
        self.api_key: str = str(config.get(CONF_API_KEY, "")).strip()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def test_connection(self) -> None:
        """Test FoxESS API token and device SN."""
        if not self.device_sn or not self.api_key:
            raise SolmateAuthError("FoxESS Device SN and API Key are required.")

        url = f"{self.BASE_URL}/op/v0/device/real/query"
        payload = {"sn": self.device_sn, "variables": ["SoC"]}

        try:
            async with self.session.post(
                url, json=payload, headers=self._headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Invalid FoxESS API Key or Device SN.")
                if resp.status != 200:
                    raise SolmateApiError(f"FoxESS API error HTTP {resp.status}")
                data = await resp.json()
                errno = data.get("errno", -1)
                if errno != 0:
                    raise SolmateAuthError(data.get("msg") or f"FoxESS error code {errno}")
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot connect to FoxESS API: {ex}") from ex

    async def get_energy_flow(self) -> EnergyFlowData:
        """Query real-time device flow variables."""
        url = f"{self.BASE_URL}/op/v0/device/real/query"
        payload = {
            "sn": self.device_sn,
            "variables": [
                "SoC",
                "pvPower",
                "batChargePower",
                "batDischargePower",
                "gridConsumptionPower",
                "loadsPower",
                "generationToday",
                "feedinToday",
                "gridConsumptionToday",
            ],
        }

        try:
            async with self.session.post(
                url, json=payload, headers=self._headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status in (401, 403):
                    raise SolmateAuthError("Invalid FoxESS credentials.")
                if resp.status != 200:
                    raise SolmateApiError(f"FoxESS error HTTP {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"FoxESS connection failed: {ex}") from ex

        soc: float = 0.0
        pv_watts: float = 0.0
        bat_charge_watts: float = 0.0
        bat_discharge_watts: float = 0.0
        grid_watts: float = 0.0
        load_watts: float = 0.0
        daily_pv: float | None = None
        daily_grid_import: float | None = None
        daily_grid_export: float | None = None

        result_list = data.get("result") or []
        first_device = result_list[0] if result_list else {}
        datas = first_device.get("datas") or []

        for item in datas:
            var = str(item.get("variable") or "").lower()
            val_raw = float(item.get("value") or 0.0)
            val_watts = val_raw * 1000.0  # FoxESS returns power in kW

            if var == "soc":
                soc = val_raw / 100.0
            elif var == "pvpower":
                pv_watts = val_watts
            elif var == "batchargepower":
                bat_charge_watts = val_watts
            elif var == "batdischargepower":
                bat_discharge_watts = val_watts
            elif var == "gridconsumptionpower":
                grid_watts = val_watts
            elif var == "loadspower":
                load_watts = val_watts
            elif var == "generationtoday":
                daily_pv = val_raw
            elif var == "gridconsumptiontoday":
                daily_grid_import = val_raw
            elif var == "feedintoday":
                daily_grid_export = val_raw

        batt_watts = -bat_charge_watts if bat_charge_watts > 0 else bat_discharge_watts

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc)),
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=round(pv_watts, 1),
            batt_power=round(batt_watts, 1),
            grid_power=round(grid_watts, 1),
            load_power=round(load_watts, 1),
            daily_pv_yield_kwh=round(daily_pv, 2) if daily_pv is not None else None,
            daily_grid_import_kwh=round(daily_grid_import, 2) if daily_grid_import is not None else None,
            daily_grid_export_kwh=round(daily_grid_export, 2) if daily_grid_export is not None else None,
        )
