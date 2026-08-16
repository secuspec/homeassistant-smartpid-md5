"""Constants for the SmartPID M5 PRO integration."""

from __future__ import annotations

DOMAIN = "smartpid_md5"

CONF_DEVICE_ID = "device_id"
CONF_NAME = "name"
# Legacy option key. Cleanup used to be a persistent boolean option; it is now a
# one-shot button entity (see button.py). This constant is kept only so setup can
# strip the stale flag from older config entries during migration.
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

# Per-channel setpoint limits (°C). These bound the setpoint number entity (and
# therefore the dashboard slider + input box). Configurable via the options flow,
# pre-filled with the machine's documented maxima. The device itself accepts a
# much wider range ([-200, 450]); these are operating limits, not the hard cap.
CONF_CH1_MIN = "ch1_min"
CONF_CH1_MAX = "ch1_max"
CONF_CH2_MIN = "ch2_min"
CONF_CH2_MAX = "ch2_max"

DEFAULT_CH1_MIN = 0.0
DEFAULT_CH1_MAX = 98.0
DEFAULT_CH2_MIN = 0.0
DEFAULT_CH2_MAX = 128.0

SETPOINT_STEP = 0.1

# Prefix for the deterministic object_id / entity_id of every entity, so a
# pre-built dashboard can reference e.g. number.smartpid_ch1_setpoint reliably.
OBJECT_ID_PREFIX = "smartpid"
