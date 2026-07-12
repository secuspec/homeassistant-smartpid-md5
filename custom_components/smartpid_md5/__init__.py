"""SmartPID M5 PRO — publishes MQTT discovery configs so HA creates the entities."""

from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_CLEANUP, CONF_DEVICE_ID, CONF_NAME, DEFAULT_NAME
from .discovery import (
    async_clear_discovery,
    async_publish_discovery,
    build_discovery_messages,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Publish (or, in cleanup mode, remove) the SmartPID discovery topics."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT integration is not available yet")

    device_id = entry.data[CONF_DEVICE_ID]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    messages = build_discovery_messages(device_id, name)

    if entry.options.get(CONF_CLEANUP, False):
        _LOGGER.info(
            "Cleanup enabled — clearing %d SmartPID discovery topics for %s",
            len(messages),
            device_id,
        )
        await async_clear_discovery(hass, messages)
    else:
        _LOGGER.info(
            "Publishing %d SmartPID discovery topics for %s", len(messages), device_id
        )
        await async_publish_discovery(hass, messages)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change so the cleanup toggle takes effect immediately."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nothing to tear down locally; retained topics are managed explicitly."""
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear the retained discovery topics when the integration is removed."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        _LOGGER.warning("MQTT unavailable — SmartPID discovery topics were not cleared")
        return
    device_id = entry.data[CONF_DEVICE_ID]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    await async_clear_discovery(hass, build_discovery_messages(device_id, name))
