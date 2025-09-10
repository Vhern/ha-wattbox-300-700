from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_OUTLETS,
    CONF_SCAN_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_OUTLETS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERIFY_SSL,
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=f"WattBox 300/700 ({user_input[CONF_HOST]})",
                data=user_input
            )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_OUTLETS, default=DEFAULT_OUTLETS): int,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self._entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        data = self._entry.data
        opts = self._entry.options or {}

        if user_input is not None:
            # Build new data; keep old password if left blank
            new_pw = user_input.get(CONF_PASSWORD, "")
            merged_data = {
                CONF_HOST: user_input.get(CONF_HOST, data.get(CONF_HOST)),
                CONF_USERNAME: user_input.get(CONF_USERNAME, data.get(CONF_USERNAME)),
                CONF_PASSWORD: data.get(CONF_PASSWORD) if new_pw == "" else new_pw,
                CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)),
                # Keep these in data so setup uses them directly
                CONF_OUTLETS: user_input.get(CONF_OUTLETS, data.get(CONF_OUTLETS, DEFAULT_OUTLETS)),
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            }

            # Persist
            self.hass.config_entries.async_update_entry(self._entry, data=merged_data, options={})
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
            vol.Required(CONF_USERNAME, default=data.get(CONF_USERNAME, "")): str,
            # Leave blank to keep existing
            vol.Optional(CONF_PASSWORD, default=""): str,
            vol.Optional(CONF_VERIFY_SSL, default=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)): bool,
            vol.Optional(CONF_OUTLETS, default=data.get(CONF_OUTLETS, DEFAULT_OUTLETS)): int,
            vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int
        })
        return self.async_show_form(step_id="init", data_schema=schema)
