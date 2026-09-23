"""Solmate Cloud Gateway API client and telemetry data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import random
from typing import Any

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore

try:
    from .const import DEFAULT_GATEWAY_URL
except ImportError:
    from const import DEFAULT_GATEWAY_URL

_LOGGER = logging.getLogger(__name__)


class SolmateError(Exception):
    """Base exception for Solmate errors."""


class SolmateAuthError(SolmateError):
    """Exception raised when authentication fails."""


class SolmateConnectionError(SolmateError):
    """Exception raised when connection to the API fails."""


class SolmateApiError(SolmateError):
    """Exception raised when an API endpoint returns an error."""


@dataclass
class EnergyFlowData:
    """Normalized real-time solar and battery telemetry model."""

    percentage: float  # 0.0 to 1.0
    is_connected: bool
    last_updated: datetime
    status_message: str | None = None

    # Realtime Power Metrics (Watts)
    pv_power: float | None = None  # Solar generation
    batt_power: float | None = None  # Negative = charging, positive = discharging
    grid_power: float | None = None  # Positive = import, negative = export
    load_power: float | None = None  # Home consumption

    # Daily Cumulative Energy Metrics (kWh)
    daily_pv_yield_kwh: float | None = None
    daily_grid_import_kwh: float | None = None
    daily_grid_export_kwh: float | None = None
    daily_load_kwh: float | None = None
    daily_batt_charge_kwh: float | None = None
    daily_batt_discharge_kwh: float | None = None

    @property
    def is_charging(self) -> bool:
        """Return True if battery is actively charging (> 10W flow into battery)."""
        if self.batt_power is None:
            return False
        return self.batt_power < -10.0

    @property
    def is_discharging(self) -> bool:
        """Return True if battery is actively discharging (> 10W flow from battery)."""
        if self.batt_power is None:
            return False
        return self.batt_power > 10.0

    @property
    def solar_independence_score(self) -> int:
        """Calculate percentage of self-reliance from solar and battery vs grid."""
        if self.daily_load_kwh and self.daily_load_kwh > 0.1:
            grid_import = self.daily_grid_import_kwh or 0.0
            self_supplied = max(0.0, self.daily_load_kwh - grid_import)
            ratio = min(1.0, max(0.0, self_supplied / self.daily_load_kwh))
            return int(round(ratio * 100.0))

        if self.load_power and self.load_power > 50.0:
            grid_w = max(0.0, self.grid_power or 0.0)
            self_w = max(0.0, self.load_power - grid_w)
            ratio = min(1.0, max(0.0, self_w / self.load_power))
            return int(round(ratio * 100.0))

        return 100

    def eta_string(self, battery_capacity_kwh: float = 10.0) -> str:
        """Calculate human-readable time-to-full or time-to-empty projection."""
        if self.percentage >= 0.99:
            return "Fully Charged"

        if self.batt_power is None or abs(self.batt_power) <= 20.0:
            return "Idle"

        if self.batt_power < -20.0:
            # Charging into battery
            remaining_wh = (1.0 - self.percentage) * battery_capacity_kwh * 1000.0
            charge_rate_watts = abs(self.batt_power)
            total_hours = remaining_wh / charge_rate_watts

            if total_hours < 0.16:
                return "Full in < 10m"
            if total_hours < 1.0:
                mins = int(round(total_hours * 60.0))
                return f"Full in {mins}m"
            hours = int(total_hours)
            mins = int(round((total_hours - float(hours)) * 60.0))
            return f"Full in {hours}h {mins}m" if mins > 0 else f"Full in {hours}h"

        if self.batt_power > 20.0:
            # Discharging from battery (10% reserve cutoff)
            usable_percent = max(0.0, self.percentage - 0.10)
            usable_wh = usable_percent * battery_capacity_kwh * 1000.0
            discharge_rate_watts = self.batt_power
            total_hours = usable_wh / discharge_rate_watts

            if total_hours < 1.0:
                mins = max(1, int(round(total_hours * 60.0)))
                return f"{mins}m left"
            hours = int(total_hours)
            mins = int(round((total_hours - float(hours)) * 60.0))
            return f"{hours}h {mins}m left" if mins > 0 else f"{hours}h left"

        return "Idle"


class SolmateApiClient:
    """Async client for Solmate cloud telemetry."""

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        base_url: str = DEFAULT_GATEWAY_URL,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._owns_session = False
        self._base_url = base_url.rstrip("/")
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.plant_id: int | None = None
        self.plant_name: str | None = None
        self._plants_cache: list[dict[str, Any]] = []

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        """Close owned session if applicable."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def login(self, email: str, password: str) -> str:
        """Authenticate with the Solmate API."""
        normalized_email = email.strip().lower()
        if normalized_email == "demo@solmate.app" or "demo" in normalized_email:
            _LOGGER.info("Using demo mode for account: %s", email)
            self.access_token = "demo_token"
            self.plant_id = 9999
            self.plant_name = "Solmate Demo Plant"
            self._plants_cache = [{"id": 9999, "name": "Solmate Demo Plant", "etoday": 16.4}]
            return self.access_token

        session = await self._get_session()
        url = f"{self._base_url}/v1/auth"
        payload = {"username": email, "password": password}

        try:
            async with session.post(url, json=payload, timeout=20) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 401:
                    msg = data.get("message") or "Invalid username or password."
                    raise SolmateAuthError(msg)
                if resp.status != 200:
                    msg = data.get("message") or f"Gateway returned HTTP {resp.status}"
                    raise SolmateConnectionError(msg)
        except aiohttp.ClientError as err:
            raise SolmateConnectionError(f"Network error connecting to Solmate gateway: {err}") from err

        if not data.get("success") or not data.get("access_token"):
            msg = data.get("message") or "Authentication failed"
            raise SolmateAuthError(msg)

        self.access_token = str(data["access_token"])
        self.refresh_token = data.get("refresh_token")
        if data.get("plant_id") is not None:
            self.plant_id = int(data["plant_id"])
        self.plant_name = data.get("plant_name")
        self._plants_cache = data.get("plants", [])
        return self.access_token

    async def get_plants(self) -> list[dict[str, Any]]:
        """Fetch list of user plants cached from login."""
        if self._plants_cache:
            return self._plants_cache

        if not self.access_token:
            raise SolmateAuthError("Not logged in.")

        if self.access_token == "demo_token":
            return [{"id": 9999, "name": "Solmate Demo Plant", "etoday": 16.4}]

        if self.plant_id is not None:
            return [{"id": self.plant_id, "name": self.plant_name or "Solar Plant", "etoday": None}]

        return []

    async def get_realtime_flow(self) -> EnergyFlowData:
        """Fetch current real-time energy flow metrics via edge gateway."""
        if not self.access_token:
            raise SolmateAuthError("Not logged in.")

        if self.access_token == "demo_token":
            return self._generate_demo_flow()

        plant_id = self.plant_id or 9999
        url = f"{self._base_url}/v1/telemetry"
        params = {"plant_id": str(plant_id)}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        session = await self._get_session()

        try:
            async with session.get(url, headers=headers, params=params, timeout=15) as resp:
                if resp.status == 401:
                    raise SolmateAuthError("Access token expired (401).")
                if resp.status != 200:
                    raise SolmateConnectionError(
                        f"Failed to fetch flow metrics: HTTP {resp.status}"
                    )
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            if self.access_token == "demo_token":
                return self._generate_demo_flow()
            raise SolmateConnectionError(f"Network error fetching energy flow: {err}") from err

        if not data.get("success"):
            if self.access_token == "demo_token":
                return self._generate_demo_flow()
            msg = data.get("message") or "Gateway failed to return telemetry"
            raise SolmateApiError(msg)

        raw_percentage = data.get("percentage")
        soc_ratio = float(raw_percentage) if raw_percentage is not None else 0.0

        return EnergyFlowData(
            percentage=max(0.0, min(1.0, soc_ratio)),
            is_connected=bool(data.get("is_connected", True)),
            last_updated=datetime.now(timezone.utc),
            pv_power=data.get("pv_power"),
            batt_power=data.get("batt_power"),
            grid_power=data.get("grid_power"),
            load_power=data.get("load_power"),
            daily_pv_yield_kwh=data.get("daily_pv_yield_kwh"),
            daily_grid_import_kwh=data.get("daily_grid_import_kwh"),
            daily_grid_export_kwh=data.get("daily_grid_export_kwh"),
            daily_batt_charge_kwh=data.get("daily_batt_charge_kwh"),
            daily_batt_discharge_kwh=data.get("daily_batt_discharge_kwh"),
            daily_load_kwh=data.get("daily_load_kwh"),
        )

    def _generate_demo_flow(self) -> EnergyFlowData:
        """Synthesize realistic solar and battery flow for offline demo testing."""
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


# Backward compatibility alias
SunsynkApiClient = SolmateApiClient
