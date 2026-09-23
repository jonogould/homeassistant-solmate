"""The Solmate Home Assistant integration."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
try:
    from homeassistant.components.http import StaticPathConfig
except ImportError:
    StaticPathConfig = None

from .const import CARD_FILENAME, CARD_URL, DOMAIN, PLATFORMS
from .coordinator import SolmateDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_register_card_path(hass: HomeAssistant) -> None:
    """Register static path for Lovelace card if not already registered."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("static_path_registered"):
        return

    card_path = Path(__file__).parent / "www" / CARD_FILENAME
    if not card_path.exists():
        return

    http = getattr(hass, "http", None)
    if http is None:
        return

    try:
        if hasattr(http, "async_register_static_paths") and StaticPathConfig is not None:
            await http.async_register_static_paths(
                [StaticPathConfig(CARD_URL, str(card_path), False)]
            )
            domain_data["static_path_registered"] = True
            _LOGGER.debug("Registered static path (async) %s -> %s", CARD_URL, card_path)
        elif hasattr(http, "register_static_path"):
            http.register_static_path(
                CARD_URL,
                str(card_path),
                cache_headers=False,
            )
            domain_data["static_path_registered"] = True
            _LOGGER.debug("Registered static path (sync) %s -> %s", CARD_URL, card_path)
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.warning("Could not register static path for Solmate card: %s", ex)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Solmate component."""
    hass.data.setdefault(DOMAIN, {})
    await async_register_card_path(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solmate from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await async_register_card_path(hass)

    coordinator = SolmateDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates (such as scan_interval or battery_capacity)
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator and coordinator.client:
            await coordinator.client.close()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
