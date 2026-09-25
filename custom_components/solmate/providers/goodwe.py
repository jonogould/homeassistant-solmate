"""GoodWe SEMS Portal API provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

import aiohttp

try:
    from ..const import CONF_ACCOUNT, CONF_PASSWORD, CONF_STATION_ID
    from ..sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from const import CONF_ACCOUNT, CONF_PASSWORD, CONF_STATION_ID
    from sunsynk_api import (
        EnergyFlowData,
        SolmateApiError,
        SolmateAuthError,
        SolmateConnectionError,
    )
    from providers.base import BaseSolarProvider

_LOGGER = logging.getLogger(__name__)


class GoodWeProvider(BaseSolarProvider):
    """Provider for GoodWe SEMS Portal."""

    BASE_URL = "https://www.semsportal.com/api/v2"

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize GoodWe provider."""
        super().__init__(session, config)
        self.account: str = str(config.get(CONF_ACCOUNT, "")).strip()
        self.password: str = str(config.get(CONF_PASSWORD, "")).strip()
        self.station_id: str = str(config.get(CONF_STATION_ID, "")).strip()
        self._token: str | None = None
        self._uid: str | None = None
        self._timestamp: int = 0

    async def _login(self) -> None:
        """Authenticate with GoodWe SEMS Portal."""
        if not self.account or not self.password:
            raise SolmateAuthError("GoodWe Account (email) and Password are required.")

        url = f"{self.BASE_URL}/Common/CrossLogin"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Token": json.dumps({"version": "v2.1.0", "client": "ios", "language": "en"}),
        }
        payload = {"account": self.account, "pwd": self.password}

        try:
            async with self.session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    raise SolmateApiError(f"GoodWe login failed HTTP {resp.status}")
                data = await resp.json()
                code = data.get("code")
                res_data = data.get("data") or {}

                if code != 0 or not res_data.get("token"):
                    msg = data.get("msg") or "Invalid GoodWe account or password."
                    raise SolmateAuthError(msg)

                self._token = res_data.get("token")
                self._uid = res_data.get("uid")
                self._timestamp = int(res_data.get("timestamp") or 0)
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"Cannot connect to GoodWe SEMS: {ex}") from ex

    async def test_connection(self) -> None:
        """Test credentials by logging in."""
        await self._login()

    async def get_energy_flow(self) -> EnergyFlowData:
        """Fetch real-time station flow."""
        if not self._token:
            await self._login()

        url = f"{self.BASE_URL}/PowerStation/GetMonitorDetailByPowerstationId"
        token_header = json.dumps({
            "version": "v2.1.0",
            "client": "ios",
            "language": "en",
            "timestamp": self._timestamp,
            "uid": self._uid,
            "token": self._token,
        })
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Token": token_header,
        }
        target_id = self.station_id if self.station_id else (self._uid or "")
        payload = {"powerStationId": target_id}

        try:
            async with self.session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 401:
                    # Token expired, re-login once
                    await self._login()
                    return await self.get_energy_flow()
                if resp.status != 200:
                    raise SolmateApiError(f"GoodWe monitor error HTTP {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as ex:
            raise SolmateConnectionError(f"GoodWe connection failed: {ex}") from ex

        res_data = data.get("data") or {}
        pdata = res_data.get("pdata") or {}
        kpi = res_data.get("kpi") or {}

        soc_raw = res_data.get("soc") if res_data.get("soc") is not None else pdata.get("soc")
        soc = float(soc_raw or 0.0) / 100.0

        pv_watts = float(res_data.get("pac") or pdata.get("pv") or 0.0)
        batt_watts = float(pdata.get("battery") or pdata.get("bettery") or 0.0)
        load_watts = float(pdata.get("load") or 0.0)
        grid_watts = float(pdata.get("grid") or 0.0)
        daily_pv = float(kpi.get("pacToday") or 0.0) if kpi.get("pacToday") is not None else None

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
