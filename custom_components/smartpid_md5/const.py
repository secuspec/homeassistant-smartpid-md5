"""Constants for the SmartPID M5 PRO integration."""

from __future__ import annotations

DOMAIN = "smartpid_md5"

CONF_DEVICE_ID = "device_id"
CONF_NAME = "name"
CONF_CLEANUP = "cleanup"

DEFAULT_NAME = "SmartPID M5 PRO"

# Home Assistant MQTT discovery prefix (must match the MQTT integration setting).
DISCOVERY_PREFIX = "homeassistant"

# Fixed topic base for the PRO model; only the 14-char <id> hash is variable.
TOPIC_BASE = "smartpidM5/pro"

MANUFACTURER = "SmartPID"
MODEL = "M5 PRO"

# Two physical channels on the PRO controller.
CHANNELS = ("CH1", "CH2")

# Command temperature range for PRO in °C, per the MQTT spec ([-200, 450]).
TEMP_MIN = -200
TEMP_MAX = 450
TEMP_STEP = 0.1
