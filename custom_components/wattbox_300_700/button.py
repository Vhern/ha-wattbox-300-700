from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_MODEL,
    CONF_OUTLETS,
    DEFAULT_MODEL,
    outlets_for,
    CONF_MODEL as _CONF_MODEL,
)
from .api import WattBoxHTTPClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback) -> None:
    client: WattBoxHTTPClient = hass.data[DOMAIN][entry.entry_id]["client"]

    model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
    outlets = entry.data.get(CONF_OUTLETS) or outlets_for(model)
    if not outlets or outlets < 1:
        outlets = outlets_for(model or DEFAULT_MODEL)

    names: List[str] = []
    try:
        names = await client.get_outlet_names()
    except Exception as e:
        _LOGGER.debug("Could not load outlet names for buttons: %s", e)

    entities: list[ButtonEntity] = []
    for i in range(outlets):
        n = i + 1
        label = f"{n} - {names[i]} Reset" if i < len(names) and names[i] else f"Outlet {n} Reset"
        entities.append(WBResetButton(client, entry, n, label))

    entities.append(WBResetAllButton(client, entry, "Reset All Outlets"))

    add_entities(entities, True)


class WBBase(ButtonEntity):
    """Base that refreshes and can optimistically update the switch coordinator"""

    def __init__(self, client: WattBoxHTTPClient, entry: ConfigEntry, name: str, unique_suffix: str):
        self._client = client
        self._entry = entry
        self._attr_name = name
        self._attr_unique_id = f"wb_300_700_{entry.data.get('host')}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
            "name": f"WattBox 300/700 ({entry.data.get('host')})",
            "manufacturer": "Snap One",
            "model": entry.data.get("model", DEFAULT_MODEL),
        }

    def _get_coordinator(self):
        try:
            return self.hass.data[DOMAIN][self._entry.entry_id].get("switch_coordinator")
        except Exception:
            return None

    async def _refresh_now(self) -> Optional[list]:
        # Use async_refresh() to perform the update immediately
        coord = self._get_coordinator()
        if not coord:
            return None
        try:
            await coord.async_refresh()
            return coord.data
        except Exception:
            return None

    def _optimistic_set(self, indices_off: list[int]) -> None:
        # Immediately set given outlet indices to OFF and push update
        coord = self._get_coordinator()
        if not coord:
            return
        try:
            data = list(coord.data or [])
            changed = False
            for idx in indices_off:
                if idx < len(data):
                    if data[idx] is True:
                        changed = True
                    data[idx] = False
            if changed:
                coord.async_set_updated_data(data)
        except Exception:
            pass


class WBResetButton(WBBase):
    """Reset one outlet: set OFF immediately, then refresh every 1s until ON"""

    def __init__(self, client: WattBoxHTTPClient, entry: ConfigEntry, outlet: int, label: str):
        super().__init__(client, entry, label, f"outlet_{outlet}_reset")
        self._outlet = outlet

    async def async_press(self) -> None:
        await self._client.reset_outlet(self._outlet)

        # Optimistic OFF now
        self._optimistic_set([self._outlet - 1])

        # Then poll every 1s with immediate refresh until ON or timeout
        for _ in range(120):
            await asyncio.sleep(1)
            data = await self._refresh_now()
            try:
                idx = self._outlet - 1
                if isinstance(data, list) and idx < len(data) and bool(data[idx]):
                    break
            except Exception:
                pass


class WBResetAllButton(WBBase):
    """Reset all outlets: set all OFF immediately, then refresh every 1s until all ON"""

    def __init__(self, client: WattBoxHTTPClient, entry: ConfigEntry, label: str):
        super().__init__(client, entry, label, "reset_all")

    async def async_press(self) -> None:
        await self._client.reset_outlet(0)

        # Optimistic OFF for all known outlets
        coord = self._get_coordinator()
        count = len(coord.data) if coord and isinstance(coord.data, list) else 12
        self._optimistic_set(list(range(count)))

        for _ in range(180):
            await asyncio.sleep(1)
            data = await self._refresh_now()
            try:
                if isinstance(data, list) and len(data) >= count and all(bool(x) for x in data[:count]):
                    break
            except Exception:
                pass