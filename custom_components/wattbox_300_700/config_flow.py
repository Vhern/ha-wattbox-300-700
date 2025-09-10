from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_VERIFY_SSL,
    CONF_SCAN_INTERVAL,
    CONF_OUTLETS,
    CONF_MODEL,
    DEFAULT_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MODEL,
    MODEL_CHOICES,
    outlets_for,
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            model = user_input[CONF_MODEL]
            data = {
                CONF_HOST: user_input[CONF_HOST],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                CONF_MODEL: model,
                CONF_OUTLETS: outlets_for(model),
            }
            return self.async_create_entry(
                title=f"WattBox 300/700 ({data[CONF_HOST]})",
                data=data,
            )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_MODEL, default=DEFAULT_MODEL): vol.In(list(MODEL_CHOICES.keys())),
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
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

        if user_input is not None:
            new_pw = user_input.get(CONF_PASSWORD, "")
            model = user_input.get(CONF_MODEL, data.get(CONF_MODEL, DEFAULT_MODEL))
            merged = {
                CONF_HOST: user_input.get(CONF_HOST, data.get(CONF_HOST)),
                CONF_USERNAME: user_input.get(CONF_USERNAME, data.get(CONF_USERNAME)),
                CONF_PASSWORD: data.get(CONF_PASSWORD) if new_pw == "" else new_pw,
                CONF_VERIFY_SSL: user_input.get(CONF_VERIFY_SSL, data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)),
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
                CONF_MODEL: model,
                CONF_OUTLETS: outlets_for(model),
            }
            self.hass.config_entries.async_update_entry(self._entry, data=merged, options={})
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            return self.async_create_entry(title="", data={})

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
            vol.Required(CONF_USERNAME, default=data.get(CONF_USERNAME, "")): str,
            vol.Optional(CONF_PASSWORD, default=""): str,  # leave blank to keep
            vol.Required(CONF_MODEL, default=data.get(CONF_MODEL, DEFAULT_MODEL)): vol.In(list(MODEL_CHOICES.keys())),
            vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
            vol.Optional(CONF_VERIFY_SSL, default=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)): bool,
        })
        return self.async_show_form(step_id="init", data_schema=schema)