"""Build and (un)publish MQTT discovery messages for a SmartPID M5 PRO device.

This integration does not create entities itself. Instead it publishes Home
Assistant MQTT *discovery* configs (retained) to the broker; HA's built-in MQTT
integration then creates the entities and binds them to the SmartPID's own
topics. Because every topic is deterministic from the device id, the exact same
message list is used to publish (retained payload) and to clear (empty payload).
"""

from __future__ import annotations

import json
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant

from .const import (
    CHANNELS,
    DISCOVERY_PREFIX,
    MANUFACTURER,
    MODEL,
    TEMP_MAX,
    TEMP_MIN,
    TEMP_STEP,
    TOPIC_BASE,
)

ORIGIN = {"name": "smartpid_md5"}


def _device_block(device_id: str, name: str) -> dict[str, Any]:
    return {
        "identifiers": [f"smartpidM5_pro_{device_id}"],
        "name": name,
        "manufacturer": MANUFACTURER,
        "model": MODEL,
    }


def build_discovery_messages(device_id: str, name: str) -> list[dict[str, Any]]:
    """Return a list of ``{"topic", "payload"}`` discovery messages.

    Note on ``value_template`` defaults: the PRO ``dynamic/CHx`` payload has two
    shapes. In *monitor* mode only ``temp``/``unit``/``runmode`` are present; the
    fields ``SP``/``mode``/``pwm``/``countdown``/``countup`` appear only in *run*
    mode. Every optional field is therefore guarded with ``default('')`` so the
    entity is not fed a stray value when the field is absent.
    """
    base = f"{TOPIC_BASE}/{device_id}"
    dev_ident = f"smartpidM5_pro_{device_id}"
    device = _device_block(device_id, name)
    status_topic = f"{base}/status"
    cmd_topic = f"{base}/commands"
    messages: list[dict[str, Any]] = []

    def add(component: str, slug: str, payload: dict[str, Any]) -> None:
        full = {
            **payload,
            "unique_id": f"{dev_ident}_{slug}",
            "device": device,
            "origin": ORIGIN,
        }
        topic = f"{DISCOVERY_PREFIX}/{component}/{dev_ident}/{slug}/config"
        messages.append({"topic": topic, "payload": full})

    # ---- per-channel entities (CH1 / CH2) --------------------------------
    for ch in CHANNELS:
        cl = ch.lower()
        dyn = f"{base}/dynamic/{ch}"

        add("sensor", f"{cl}_temp", {
            "name": f"{ch} Temperature",
            "state_topic": dyn,
            "value_template": "{{ value_json.temp | default('') }}",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
        })
        add("sensor", f"{cl}_setpoint_state", {
            "name": f"{ch} Setpoint (readback)",
            "state_topic": dyn,
            "value_template": "{{ value_json.SP | default('') }}",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        })
        add("sensor", f"{cl}_pwm", {
            "name": f"{ch} Power",
            "state_topic": dyn,
            "value_template": "{{ value_json.pwm | default('') }}",
            "unit_of_measurement": "%",
            "state_class": "measurement",
            "icon": "mdi:fire",
        })
        add("sensor", f"{cl}_mode", {
            "name": f"{ch} Mode",
            "state_topic": dyn,
            "value_template": "{{ value_json.mode | default('') }}",
            "icon": "mdi:thermostat",
        })
        add("sensor", f"{cl}_runmode", {
            "name": f"{ch} Run Mode",
            "state_topic": dyn,
            "value_template": "{{ value_json.runmode | default('') }}",
            "icon": "mdi:play-circle-outline",
        })
        add("sensor", f"{cl}_countdown", {
            "name": f"{ch} Countdown",
            "state_topic": dyn,
            "value_template": "{{ value_json.countdown | default('') }}",
            "unit_of_measurement": "s",
            "device_class": "duration",
        })
        add("sensor", f"{cl}_countup", {
            "name": f"{ch} Countup",
            "state_topic": dyn,
            "value_template": "{{ value_json.countup | default('') }}",
            "unit_of_measurement": "s",
            "device_class": "duration",
        })
        add("number", f"{cl}_setpoint", {
            "name": f"{ch} Setpoint",
            "state_topic": dyn,
            "value_template": "{{ value_json.SP | default('') }}",
            "command_topic": cmd_topic,
            "command_template": '{"' + ch + ' SP": {{ value }} }',
            "min": TEMP_MIN,
            "max": TEMP_MAX,
            "step": TEMP_STEP,
            "mode": "box",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        })
        add("select", f"{cl}_profile", {
            "name": f"{ch} Profile",
            "command_topic": cmd_topic,
            "command_template": '{"' + ch + ' profile": {{ value }} }',
            "options": [str(i) for i in range(1, 11)],
            "icon": "mdi:format-list-numbered",
        })
        add("switch", f"{cl}_run", {
            "name": f"{ch} Run",
            "state_topic": dyn,
            "value_template": (
                "{{ 'OFF' if value_json.runmode | default('monitor') == 'monitor' "
                "else 'ON' }}"
            ),
            "state_on": "ON",
            "state_off": "OFF",
            "command_topic": cmd_topic,
            "payload_on": json.dumps({f"{ch} profile": 1, "start": "standard"}),
            "payload_off": json.dumps({"stop": True}),
            "icon": "mdi:power",
        })

    # ---- device-level diagnostic + event entities (once) -----------------
    add("sensor", "ip", {
        "name": "IP Address",
        "state_topic": status_topic,
        "value_template": "{{ value_json.client | default('') }}",
        "entity_category": "diagnostic",
        "icon": "mdi:ip-network",
    })
    add("sensor", "ssid", {
        "name": "Wi-Fi SSID",
        "state_topic": status_topic,
        "value_template": "{{ value_json.SSID | default('') }}",
        "entity_category": "diagnostic",
        "icon": "mdi:wifi",
    })
    add("sensor", "serial", {
        "name": "Serial",
        "state_topic": status_topic,
        "value_template": "{{ value_json.serial | default('') }}",
        "entity_category": "diagnostic",
        "icon": "mdi:identifier",
    })
    add("sensor", "event_standard", {
        "name": "Last Event (standard)",
        "state_topic": f"{base}/events/standard",
        "value_template": "{{ value_json.event | default('') }}",
        "icon": "mdi:message-alert-outline",
    })
    add("sensor", "event_advanced", {
        "name": "Last Event (advanced)",
        "state_topic": f"{base}/events/advanced",
        "value_template": "{{ value_json.event | default('') }}",
        "icon": "mdi:message-alert-outline",
    })

    return messages


async def async_publish_discovery(
    hass: HomeAssistant, messages: list[dict[str, Any]]
) -> None:
    """Publish each discovery config retained so HA (re)discovers it on restart."""
    for msg in messages:
        await mqtt.async_publish(
            hass, msg["topic"], json.dumps(msg["payload"]), qos=0, retain=True
        )


async def async_clear_discovery(
    hass: HomeAssistant, messages: list[dict[str, Any]]
) -> None:
    """Remove the discovery configs from the broker.

    A zero-byte payload published with ``retain=True`` clears the broker's
    retained message (per the MQTT spec) and makes HA drop the entity. Publishing
    empty *without* retain would only remove it live, leaving the old retained
    config to be replayed on the next restart.
    """
    for msg in messages:
        await mqtt.async_publish(hass, msg["topic"], "", qos=0, retain=True)
