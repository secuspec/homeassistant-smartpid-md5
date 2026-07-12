"""Config and options flow for the SmartPID M5 PRO integration."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback

try:  # HA >= 2024.4
    from homeassistant.config_entries import ConfigFlowResult
except ImportError:  # older cores
    from homeassistant.data_entry_flow import FlowResult as ConfigFlowResult

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

# The <id> is the 14-character hex hash from the MQTT topics (e.g. a1b2c3d4e5f6a7).
_ID_RE = re.compile(r"^[0-9a-f]{14}$")


class SmartpidConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup: ask for the device id hash and a name."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip().lower()
            if not _ID_RE.match(device_id):
                errors["base"] = "invalid_id"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                name = user_input.get(CONF_NAME) or DEFAULT_NAME
                return self.async_create_entry(
                    title=name,
                    data={CONF_DEVICE_ID: device_id, CONF_NAME: name},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmartpidOptionsFlow()


class SmartpidOptionsFlow(OptionsFlow):
    """Expose the setpoint limits and the discovery-topic cleanup toggle.

    Canonical current pattern: no custom ``__init__``; the framework provides
    ``self.config_entry`` automatically.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_CH1_MIN] >= user_input[CONF_CH1_MAX]:
                errors["base"] = "ch1_range"
            elif user_input[CONF_CH2_MIN] >= user_input[CONF_CH2_MAX]:
                errors["base"] = "ch2_range"
            else:
                return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CH1_MIN, default=opts.get(CONF_CH1_MIN, DEFAULT_CH1_MIN)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CH1_MAX, default=opts.get(CONF_CH1_MAX, DEFAULT_CH1_MAX)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CH2_MIN, default=opts.get(CONF_CH2_MIN, DEFAULT_CH2_MIN)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CH2_MAX, default=opts.get(CONF_CH2_MAX, DEFAULT_CH2_MAX)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CLEANUP, default=opts.get(CONF_CLEANUP, False)
                ): bool,
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
