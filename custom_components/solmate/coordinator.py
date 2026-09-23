"""DataUpdateCoordinator for Solmate integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BATTERY_CAPACITY_KWH,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .sunsynk_api import (
    EnergyFlowData,
    SolmateApiError,
    SolmateAuthError,
    SolmateConnectionError,
    SunsynkApiClient,
)

_LOGGER = logging.getLogger(__name__)


class SolmateDataUpdateCoordinator(DataUpdateCoordinator[EnergyFlowData]):
    """Class to manage fetching Solmate data from the inverter cloud API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.email: str = entry.data[CONF_EMAIL]
        self._password: str = entry.data[CONF_PASSWORD]

        scan_interval_sec = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({self.email})",
            update_interval=timedelta(seconds=scan_interval_sec),
        )

        session = async_get_clientsession(hass)
        self.client = SunsynkApiClient(session=session)

    @property
    def battery_capacity_kwh(self) -> float:
        """Get the configured battery capacity in kWh."""
        return float(
            self.entry.options.get(
                CONF_BATTERY_CAPACITY_KWH,
                self.entry.data.get(
                    CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
                ),
            )
        )

    async def _async_update_data(self) -> EnergyFlowData:
        """Fetch real-time flow data from inverter API."""
        # 1. Login if not already authenticated
        if not self.client.access_token:
            try:
                await self.client.login(self.email, self._password)
            except SolmateAuthError as err:
                raise ConfigEntryAuthFailed(
                    f"Authentication failed for {self.email}: {err}"
                ) from err
            except SolmateConnectionError as err:
                raise UpdateFailed(f"Connection error logging in: {err}") from err

        # 2. Fetch real-time flow
        try:
            return await self.client.get_realtime_flow()
        except SolmateAuthError:
            # Token might have expired, attempt re-login once
            _LOGGER.info("Access token expired for %s, re-authenticating...", self.email)
            try:
                await self.client.login(self.email, self._password)
                return await self.client.get_realtime_flow()
            except SolmateAuthError as err:
                raise ConfigEntryAuthFailed(
                    f"Re-authentication failed for {self.email}: {err}"
                ) from err
            except Exception as err:
                raise UpdateFailed(
                    f"Failed to fetch data after re-authentication: {err}"
                ) from err
        except (SolmateConnectionError, SolmateApiError) as err:
            raise UpdateFailed(f"Error communicating with Solmate API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error updating Solmate data: {err}") from err
