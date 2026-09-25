"""The Solmate Home Assistant integration."""

from __future__ import annotations

import logging
from pathlib import Path
import shutil

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

try:
    from homeassistant.components.http import StaticPathConfig
except ImportError:
    StaticPathConfig = None

from .const import CARD_FILENAME, CARD_URL, DOMAIN, PLATFORMS, URL_BASE
from .coordinator import SolmateDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _copy_file_sync(src: Path, dest_dir: Path, filename: str) -> None:
    """Synchronous file copy helper for executor."""
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / filename
        shutil.copy2(src, dest_file)
        _LOGGER.debug("Copied Solmate card to %s", dest_file)
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.debug("Could not copy card to www: %s", ex)


async def _async_copy_card_to_local_www(hass: HomeAssistant, card_path: Path) -> None:
    """Copy card to /config/www so /local/solmate-card.js is always available."""
    try:
        www_dir = Path(hass.config.path("www"))
        await hass.async_add_executor_job(
            _copy_file_sync, card_path, www_dir, CARD_FILENAME
        )
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.debug("Could not initiate card copy to local www: %s", ex)


async def _async_auto_register_lovelace(hass: HomeAssistant) -> None:
    """Auto-register Solmate card in Lovelace resources when Home Assistant is ready."""

    async def _register_resources(_event=None) -> None:
        try:
            lovelace = hass.data.get("lovelace")
            if not lovelace:
                return
            resources = getattr(lovelace, "resources", None)
            if not resources:
                return

            if hasattr(resources, "async_items") and hasattr(resources, "async_create_item"):
                items = resources.async_items()
                existing_urls = {
                    item.get("url") for item in items if isinstance(item, dict)
                }
                # Check if already present under /solmate or /local
                if (
                    CARD_URL not in existing_urls
                    and f"/local/{CARD_FILENAME}" not in existing_urls
                ):
                    await resources.async_create_item({
                        "res_type": "module",
                        "url": CARD_URL,
                    })
                    _LOGGER.info("Auto-registered Solmate card resource: %s", CARD_URL)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.debug("Could not auto-register Lovelace resource: %s", ex)

    if hass.is_running:
        await _register_resources()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_resources)


async def async_register_card_path(hass: HomeAssistant) -> None:
    """Register static path for Lovelace card if not already registered."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("static_path_registered"):
        return

    card_dir = Path(__file__).parent / "www"
    card_path = card_dir / CARD_FILENAME
    if not card_path.exists():
        _LOGGER.warning("Solmate card file not found at %s", card_path)
        return

    http = getattr(hass, "http", None)
    if http is not None:
        try:
            if hasattr(http, "async_register_static_paths") and StaticPathConfig is not None:
                await http.async_register_static_paths([
                    StaticPathConfig(URL_BASE, str(card_dir), cache_headers=False),
                    StaticPathConfig(CARD_URL, str(card_path), cache_headers=False),
                ])
                domain_data["static_path_registered"] = True
                _LOGGER.debug("Registered static paths: %s and %s", URL_BASE, CARD_URL)
            elif hasattr(http, "register_static_path"):
                http.register_static_path(
                    CARD_URL,
                    str(card_path),
                    cache_headers=False,
                )
                domain_data["static_path_registered"] = True
                _LOGGER.debug("Registered static path (sync): %s", CARD_URL)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.warning("Could not register static path for Solmate card: %s", ex)

    # Also sync to /config/www/solmate-card.js for foolproof /local/ access
    await _async_copy_card_to_local_www(hass, card_path)

    # Auto-register in Lovelace resources so user doesn't have to manually configure it
    await _async_auto_register_lovelace(hass)


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
        if coordinator:
            if hasattr(coordinator, "async_close"):
                await coordinator.async_close()
            elif getattr(coordinator, "client", None):
                await coordinator.client.close()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

