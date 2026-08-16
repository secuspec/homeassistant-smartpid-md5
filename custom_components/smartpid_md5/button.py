"""Button entities that (re)publish or clear the SmartPID discovery topics.

The integration's whole job is to publish Home Assistant MQTT *discovery* configs
on behalf of a device that ships none. These two buttons expose that as explicit,
one-shot actions instead of a persistent option:

* **Republish** re-sends every retained discovery config. This also happens on
  every setup/reload, so the button is mainly for restoring the entities after a
  broker wipe without touching the config entry.
* **Remove** clears the configs with an empty retained payload — the
  spec-compliant way to delete a retained message — which drops the entities
  until the next publish. This replaces the old persistent ``cleanup`` option,
  whose value was re-evaluated on every setup and would silently wipe the topics
  again on each restart/reinstall.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import _limits_from_entry
from .const import CONF_DEVICE_ID, CONF_NAME, DEFAULT_NAME, MANUFACTURER, MODEL
from .discovery import (
    async_clear_discovery,
    async_publish_discovery,
    build_discovery_messages,
)

# The MQTT integration registers the device it creates from our discovery configs
# with identifiers of the shape ("mqtt", "<ident>"); matching that links our
# native buttons to the same device card instead of spawning a duplicate.
MQTT_DOMAIN = "mqtt"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the discovery-control buttons for one SmartPID device."""
    async_add_entities([SmartpidRepublishButton(entry), SmartpidClearButton(entry)])


class _SmartpidDiscoveryButton(ButtonEntity):
    """Base button bound to one SmartPID device's set of discovery configs."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    entity_description: ButtonEntityDescription

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        device_id = entry.data[CONF_DEVICE_ID]
        dev_ident = f"smartpidM5_pro_{device_id}"
        self._attr_unique_id = f"{dev_ident}_{self.entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(MQTT_DOMAIN, dev_ident)},
            name=entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    def _messages(self) -> list[dict[str, Any]]:
        """Rebuild the current discovery message list from the entry."""
        return build_discovery_messages(
            self._entry.data[CONF_DEVICE_ID],
            self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            _limits_from_entry(self._entry),
        )


class SmartpidRepublishButton(_SmartpidDiscoveryButton):
    """Re-publish all retained discovery configs to the broker."""

    entity_description = ButtonEntityDescription(
        key="republish_discovery",
        translation_key="republish_discovery",
        icon="mdi:cloud-upload-outline",
    )

    async def async_press(self) -> None:
        await async_publish_discovery(self.hass, self._messages())


class SmartpidClearButton(_SmartpidDiscoveryButton):
    """Clear all retained discovery configs from the broker."""

    entity_description = ButtonEntityDescription(
        key="remove_discovery",
        translation_key="remove_discovery",
        icon="mdi:trash-can-outline",
    )

    async def async_press(self) -> None:
        await async_clear_discovery(self.hass, self._messages())
