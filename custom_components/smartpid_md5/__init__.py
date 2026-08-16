"""SmartPID M5 PRO — publishes MQTT discovery configs so HA creates the entities."""

from __future__ import annotations

import logging

from homeassistant.components import mqtt, persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_CH1_MAX,
    CONF_CH1_MIN,
    CONF_CH2_MAX,
    CONF_CH2_MIN,
    CONF_CLEANUP,
    CONF_DEVICE_ID,
    CONF_NAME,
    DEFAULT_CH1_MAX,
    DEFAULT_CH1_MIN,
    DEFAULT_CH2_MAX,
    DEFAULT_CH2_MIN,
    DEFAULT_NAME,
    DOMAIN,
)
from .discovery import (
    async_clear_discovery,
    async_publish_discovery,
    build_discovery_messages,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON]


def _limits_from_entry(entry: ConfigEntry) -> dict[str, tuple[float, float]]:
    """Read the per-channel setpoint limits from the entry options."""
    opts = entry.options
    return {
        "CH1": (
            opts.get(CONF_CH1_MIN, DEFAULT_CH1_MIN),
            opts.get(CONF_CH1_MAX, DEFAULT_CH1_MAX),
        ),
        "CH2": (
            opts.get(CONF_CH2_MIN, DEFAULT_CH2_MIN),
            opts.get(CONF_CH2_MAX, DEFAULT_CH2_MAX),
        ),
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Publish the SmartPID discovery topics and set up the control buttons."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT integration is not available yet")

    # One-time migration. Earlier versions stored cleanup as a persistent option
    # that was re-evaluated on *every* setup: an entry left with cleanup=True (the
    # natural state after using it to tidy up before a reinstall) would silently
    # clear its own discovery topics again on each restart instead of publishing
    # them, leaving the entities present in the registry but unavailable and
    # un-enableable. Cleanup is now an explicit one-shot button, so drop the stale
    # flag and always publish.
    if CONF_CLEANUP in entry.options:
        new_options = {k: v for k, v in entry.options.items() if k != CONF_CLEANUP}
        hass.config_entries.async_update_entry(entry, options=new_options)

    device_id = entry.data[CONF_DEVICE_ID]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    messages = build_discovery_messages(device_id, name, _limits_from_entry(entry))
    _LOGGER.info(
        "Publishing %d SmartPID discovery topics for %s", len(messages), device_id
    )
    await async_publish_discovery(hass, messages)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change so new setpoint limits are re-published at once."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the control buttons; retained topics are managed explicitly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear the retained discovery topics when the integration is removed."""
    device_id = entry.data[CONF_DEVICE_ID]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    if not await mqtt.async_wait_for_mqtt_client(hass):
        # The broker is unreachable, so the retained discovery configs stay on it
        # with no config entry left to manage them. On the next HA start they would
        # re-create the entities as orphans. We cannot clear them now, so tell the
        # user exactly how to recover instead of failing silently.
        _LOGGER.warning(
            "MQTT unavailable — %d SmartPID discovery topics for %s were NOT cleared "
            "and remain retained on the broker",
            len(build_discovery_messages(device_id, name)),
            device_id,
        )
        persistent_notification.async_create(
            hass,
            (
                f"The SmartPID device `{device_id}` was removed while the MQTT "
                "broker was unreachable, so its retained discovery topics could "
                "**not** be cleared and still live on the broker.\n\n"
                "To clean them up, re-add the integration with the same device ID "
                "and press **Remove discovery topics**, or delete the "
                f"`homeassistant/+/smartpidM5_pro_{device_id}/#` topics on the "
                "broker manually."
            ),
            title="SmartPID M5 PRO — discovery topics not cleared",
            notification_id=f"{DOMAIN}_orphan_{device_id}",
        )
        return

    await async_clear_discovery(hass, build_discovery_messages(device_id, name))
