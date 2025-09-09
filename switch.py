from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_OUTLETS,
    CONF_SCAN_INTERVAL,
    DEFAULT_OUTLETS,
    DEFAULT_SCAN_INTERVAL,
)
from .api import WattBoxHTTPClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback) -> None:
    client: WattBoxHTTPClient = hass.data[DOMAIN][entry.entry_id]["client"]

    outlets = entry.options.get(CONF_OUTLETS, entry.data.get(CONF_OUTLETS, DEFAULT_OUTLETS))
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    async def _update() -> list[bool]:
        try:
            states = await client.get_outlet_states()
            if len(states) < outlets:
                states += [False] * (outlets - len(states))
            return states[:outlets]
        except Exception as e:
            raise UpdateFailed(str(e)) from e

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattbox_300_700",
        update_method=_update,
        update_interval=timedelta(seconds=scan_interval),
    )
    await coordinator.async_config_entry_first_refresh()

    entities = [WBOutletSwitch(client, coordinator, i + 1, entry) for i in range(outlets)]
    add_entities(entities, True)


class WBOutletSwitch(SwitchEntity):
    """One WattBox outlet"""

    def __init__(self, client: WattBoxHTTPClient, coordinator: DataUpdateCoordinator, outlet: int, entry: ConfigEntry):
        self._client = client
        self.coordinator = coordinator
        self._outlet = outlet
        self._entry = entry
        self._attr_name = f"WattBox Outlet {outlet}"
        self._attr_unique_id = f"wb_300_700_{entry.data.get('host')}_outlet_{outlet}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
            "name": f"WattBox 300/700 ({entry.data.get('host')})",
            "manufacturer": "Snap One",
            "model": "WattBox 300/700",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data[self._outlet - 1])

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._client.set_outlet(self._outlet, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._client.set_outlet(self._outlet, False)
        await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
