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
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PROVIDER_SUNSYNK,
)
from .providers import BaseSolarProvider, get_provider
from .sunsynk_api import (
    EnergyFlowData,
    SolmateApiError,
    SolmateAuthError,
    SolmateConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class SolmateDataUpdateCoordinator(DataUpdateCoordinator[EnergyFlowData]):
    """Class to manage fetching Solmate data from the inverter cloud/local API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.provider_type: str = entry.data.get(CONF_PROVIDER, PROVIDER_SUNSYNK)

        scan_interval_sec = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({entry.title})",
            update_interval=timedelta(seconds=scan_interval_sec),
        )

        session = async_get_clientsession(hass)
        self.provider: BaseSolarProvider = get_provider(
            self.provider_type, session=session, config=entry.data
        )
        # Backward-compatibility alias for tests/lifecycle
        self.client = getattr(self.provider, "client", None)

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

    async def async_close(self) -> None:
        """Close provider resources."""
        await self.provider.close()

    async def _async_update_data(self) -> EnergyFlowData:
        """Fetch real-time flow data from the active provider."""
        try:
            return await self.provider.get_energy_flow()
        except SolmateAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.entry.title}: {err}"
            ) from err
        except SolmateConnectionError as err:
            raise UpdateFailed(f"Connection error fetching solar flow: {err}") from err
        except SolmateApiError as err:
            raise UpdateFailed(f"Error communicating with solar API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error updating Solmate data: {err}") from err

