"""Config flow for Solmate integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_BATTERY_CAPACITY_KWH,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    PROVIDER_DEMO,
    PROVIDER_NAMES,
    PROVIDER_SUNSYNK,
)
from .sunsynk_api import SolmateAuthError, SolmateConnectionError, SunsynkApiClient

_LOGGER = logging.getLogger(__name__)


class SolmateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solmate."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._provider: str = PROVIDER_SUNSYNK
        self._email: str = ""
        self._battery_capacity: float = DEFAULT_BATTERY_CAPACITY_KWH

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial step: select provider."""
        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            if self._provider == PROVIDER_DEMO:
                return await self.async_step_demo()
            return await self.async_step_credentials()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROVIDER, default=PROVIDER_SUNSYNK): vol.In(
                        PROVIDER_NAMES
                    ),
                }
            ),
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle entering inverter account credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            # Check if this email is already registered
            await self.async_set_unique_id(f"solmate_{email.lower()}")
            self._abort_if_unique_id_configured()

            # Test credentials
            session = async_get_clientsession(self.hass)
            client = SunsynkApiClient(session=session)

            try:
                await client.login(email, password)
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error during login: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate ({email})",
                    data={
                        CONF_PROVIDER: self._provider,
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_BATTERY_CAPACITY_KWH: battery_capacity,
                    },
                )

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    async def async_step_demo(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle demo simulator configuration."""
        await self.async_set_unique_id("solmate_demo_simulator")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Solmate (Demo Simulator)",
            data={
                CONF_PROVIDER: PROVIDER_DEMO,
                CONF_EMAIL: "demo@solmate.app",
                CONF_PASSWORD: "demo",
                CONF_BATTERY_CAPACITY_KWH: DEFAULT_BATTERY_CAPACITY_KWH,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler."""
        return SolmateOptionsFlowHandler(config_entry)


class SolmateOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Solmate options."""

    def __init__(self, config_entry: config_entries.ConfigEntry | None = None) -> None:
        """Initialize options flow."""
        if config_entry is not None:
            self._custom_config_entry = config_entry

    @property
    def _entry(self) -> config_entries.ConfigEntry:
        """Return the config entry safely across Home Assistant versions."""
        if hasattr(self, "_custom_config_entry"):
            return self._custom_config_entry
        return self.config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options: scan interval and battery capacity."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self._entry
        current_scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_capacity = entry.options.get(
            CONF_BATTERY_CAPACITY_KWH,
            entry.data.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            ),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_scan_interval,
                    ): vol.All(vol.Coerce(int), vol.Clamp(min=MIN_SCAN_INTERVAL)),
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=current_capacity,
                    ): vol.Coerce(float),
                }
            ),
        )
