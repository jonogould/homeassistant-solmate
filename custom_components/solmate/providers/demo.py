"""Demo Simulator provider for Solmate."""

from __future__ import annotations

from datetime import datetime, timezone
import random
from typing import Any

import aiohttp

try:
    from ..sunsynk_api import EnergyFlowData
    from .base import BaseSolarProvider
except (ImportError, ValueError):
    from sunsynk_api import EnergyFlowData
    from providers.base import BaseSolarProvider


class DemoProvider(BaseSolarProvider):
    """Provider for simulated demo solar & battery environment."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize Demo provider."""
        super().__init__(session, config)

    async def test_connection(self) -> None:
        """Demo provider is always valid."""
        return None

    async def get_energy_flow(self) -> EnergyFlowData:
        """Generate realistic real-time telemetry based on time of day."""
        now = datetime.now()
        hour = now.hour
        is_day = 6 <= hour < 19

        if is_day:
            pv_power = round(random.uniform(2800, 4600), 1)
            load_power = round(random.uniform(450, 850), 1)
            batt_power = round(-(pv_power - load_power - random.uniform(100, 300)), 1)
            grid_power = round(-random.uniform(50, 200), 1)
            soc = round(random.uniform(0.75, 0.95), 2)
        else:
            pv_power = 0.0
            load_power = round(random.uniform(350, 750), 1)
            batt_power = round(load_power + random.uniform(20, 50), 1)
            grid_power = round(random.uniform(10, 50), 1)
            soc = round(random.uniform(0.40, 0.70), 2)

        return EnergyFlowData(
            percentage=soc,
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            pv_power=pv_power,
            batt_power=batt_power,
            grid_power=grid_power,
            load_power=load_power,
            daily_pv_yield_kwh=16.8,
            daily_grid_import_kwh=1.1,
            daily_grid_export_kwh=7.4,
            daily_load_kwh=11.2,
            daily_batt_charge_kwh=9.5,
            daily_batt_discharge_kwh=4.2,
        )
