"""Config flow for Solmate integration supporting all solar inverter providers."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_ACCOUNT,
    CONF_API_KEY,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_BATTERY_CAPACITY_KWH,
    CONF_DEVICE_SN,
    CONF_EMAIL,
    CONF_GATEWAY_IP,
    CONF_PASSWORD,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    CONF_SITE_ID,
    CONF_STATION_ID,
    CONF_TOKEN,
    CONF_USERNAME,
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    PROVIDER_DEMO,
    PROVIDER_ENPHASE,
    PROVIDER_FOXESS,
    PROVIDER_GOODWE,
    PROVIDER_GROWATT,
    PROVIDER_NAMES,
    PROVIDER_SOLAREDGE,
    PROVIDER_SOLARMAN,
    PROVIDER_SUNSYNK,
    PROVIDER_TESLA,
    PROVIDER_VICTRON,
)
from .providers import get_provider
from .sunsynk_api import SolmateAuthError, SolmateConnectionError

_LOGGER = logging.getLogger(__name__)


class SolmateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solmate across all supported inverter providers."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._provider: str = PROVIDER_SUNSYNK

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial step: select provider."""
        if user_input is not None:
            self._provider = user_input[CONF_PROVIDER]
            if self._provider == PROVIDER_DEMO:
                return await self.async_step_demo()
            if self._provider == PROVIDER_SUNSYNK:
                return await self.async_step_credentials()
            if self._provider == PROVIDER_SOLAREDGE:
                return await self.async_step_solaredge()
            if self._provider == PROVIDER_VICTRON:
                return await self.async_step_victron()
            if self._provider == PROVIDER_TESLA:
                return await self.async_step_tesla()
            if self._provider == PROVIDER_FOXESS:
                return await self.async_step_foxess()
            if self._provider == PROVIDER_GOODWE:
                return await self.async_step_goodwe()
            if self._provider == PROVIDER_GROWATT:
                return await self.async_step_growatt()
            if self._provider == PROVIDER_ENPHASE:
                return await self.async_step_enphase()
            if self._provider == PROVIDER_SOLARMAN:
                return await self.async_step_solarman()

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

    # 1. Sunsynk / Deye Cloud (step_id="credentials" for backward compatibility)
    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Sunsynk / Deye Cloud credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_{email.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_SUNSYNK,
                CONF_EMAIL: email,
                CONF_PASSWORD: password,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_SUNSYNK, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during Sunsynk login: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=f"Solmate ({email})", data=data)

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

    # 2. SolarEdge
    async def async_step_solaredge(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle SolarEdge Monitoring API credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            site_id = str(user_input[CONF_SITE_ID]).strip()
            api_key = str(user_input[CONF_API_KEY]).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_solaredge_{site_id.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_SOLAREDGE,
                CONF_SITE_ID: site_id,
                CONF_API_KEY: api_key,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_SOLAREDGE, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during SolarEdge setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate SolarEdge ({site_id})", data=data
                )

        return self.async_show_form(
            step_id="solaredge",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SITE_ID): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 3. Victron Energy
    async def async_step_victron(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Victron VRM REST API credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            site_id = str(user_input[CONF_SITE_ID]).strip()
            token = str(user_input[CONF_TOKEN]).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_victron_{site_id.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_VICTRON,
                CONF_SITE_ID: site_id,
                CONF_TOKEN: token,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_VICTRON, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during Victron setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate Victron ({site_id})", data=data
                )

        return self.async_show_form(
            step_id="victron",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SITE_ID): str,
                    vol.Required(CONF_TOKEN): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 4. Tesla Powerwall
    async def async_step_tesla(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Tesla Powerwall local gateway."""
        errors: dict[str, str] = {}

        if user_input is not None:
            gateway_ip = str(user_input[CONF_GATEWAY_IP]).strip()
            password = str(user_input.get(CONF_PASSWORD, "")).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, 13.5  # Standard Tesla Powerwall capacity
            )

            clean_ip = gateway_ip.replace("http://", "").replace("https://", "").strip("/")
            await self.async_set_unique_id(f"solmate_tesla_{clean_ip.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_TESLA,
                CONF_GATEWAY_IP: gateway_ip,
                CONF_PASSWORD: password,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_TESLA, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during Tesla setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate Powerwall ({clean_ip})", data=data
                )

        return self.async_show_form(
            step_id="tesla",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GATEWAY_IP): str,
                    vol.Optional(CONF_PASSWORD, default=""): str,
                    vol.Optional(CONF_BATTERY_CAPACITY_KWH, default=13.5): vol.Coerce(
                        float
                    ),
                }
            ),
            errors=errors,
        )

    # 5. FoxESS Cloud
    async def async_step_foxess(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle FoxESS Open API credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_sn = str(user_input[CONF_DEVICE_SN]).strip()
            api_key = str(user_input[CONF_API_KEY]).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_foxess_{device_sn.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_FOXESS,
                CONF_DEVICE_SN: device_sn,
                CONF_API_KEY: api_key,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_FOXESS, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during FoxESS setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate FoxESS ({device_sn})", data=data
                )

        return self.async_show_form(
            step_id="foxess",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_SN): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 6. GoodWe SEMS
    async def async_step_goodwe(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle GoodWe SEMS Portal account."""
        errors: dict[str, str] = {}

        if user_input is not None:
            account = str(user_input[CONF_ACCOUNT]).strip()
            password = str(user_input[CONF_PASSWORD]).strip()
            station_id = str(user_input.get(CONF_STATION_ID, "")).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_goodwe_{account.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_GOODWE,
                CONF_ACCOUNT: account,
                CONF_PASSWORD: password,
                CONF_STATION_ID: station_id,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_GOODWE, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during GoodWe setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate GoodWe ({account})", data=data
                )

        return self.async_show_form(
            step_id="goodwe",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCOUNT): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_STATION_ID, default=""): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 7. Growatt
    async def async_step_growatt(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Growatt ShineServer account."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = str(user_input[CONF_USERNAME]).strip()
            password = str(user_input[CONF_PASSWORD]).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_growatt_{username.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_GROWATT,
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_GROWATT, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during Growatt setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate Growatt ({username})", data=data
                )

        return self.async_show_form(
            step_id="growatt",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 8. Enphase Envoy
    async def async_step_enphase(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Enphase local Envoy gateway."""
        errors: dict[str, str] = {}

        if user_input is not None:
            gateway_ip = str(user_input[CONF_GATEWAY_IP]).strip()
            token = str(user_input.get(CONF_TOKEN, "")).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            clean_ip = gateway_ip.replace("http://", "").replace("https://", "").strip("/")
            await self.async_set_unique_id(f"solmate_enphase_{clean_ip.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_ENPHASE,
                CONF_GATEWAY_IP: gateway_ip,
                CONF_TOKEN: token,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_ENPHASE, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during Enphase setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate Envoy ({clean_ip})", data=data
                )

        return self.async_show_form(
            step_id="enphase",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GATEWAY_IP): str,
                    vol.Optional(CONF_TOKEN, default=""): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 9. Solarman
    async def async_step_solarman(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Solarman Open API credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            app_id = str(user_input[CONF_APP_ID]).strip()
            app_secret = str(user_input[CONF_APP_SECRET]).strip()
            station_id = str(user_input[CONF_STATION_ID]).strip()
            battery_capacity = user_input.get(
                CONF_BATTERY_CAPACITY_KWH, DEFAULT_BATTERY_CAPACITY_KWH
            )

            await self.async_set_unique_id(f"solmate_solarman_{station_id.lower()}")
            self._abort_if_unique_id_configured()

            data = {
                CONF_PROVIDER: PROVIDER_SOLARMAN,
                CONF_APP_ID: app_id,
                CONF_APP_SECRET: app_secret,
                CONF_STATION_ID: station_id,
                CONF_BATTERY_CAPACITY_KWH: battery_capacity,
            }

            session = async_get_clientsession(self.hass)
            provider = get_provider(PROVIDER_SOLARMAN, session=session, config=data)

            try:
                await provider.test_connection()
            except SolmateAuthError:
                errors["base"] = "invalid_auth"
            except SolmateConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Error during Solarman setup: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Solmate Solarman ({station_id})", data=data
                )

        return self.async_show_form(
            step_id="solarman",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APP_ID): str,
                    vol.Required(CONF_APP_SECRET): str,
                    vol.Required(CONF_STATION_ID): str,
                    vol.Optional(
                        CONF_BATTERY_CAPACITY_KWH,
                        default=DEFAULT_BATTERY_CAPACITY_KWH,
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )

    # 10. Demo Simulator
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
