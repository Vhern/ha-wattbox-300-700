from __future__ import annotations

import logging

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
)
from .api import WattBoxHTTPClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback) -> None:
    client: WattBoxHTTPClient = hass.data[DOMAIN][entry.entry_id]["client"]

    model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
    outlets = entry.data.get(CONF_OUTLETS) or outlets_for(model)
    if not outlets or outlets < 1:
        outlets = outlets_for(model or DEFAULT_MODEL)

    names: list[str] = []
    try:
        names = await client.get_outlet_names()
    except Exception as e:
        _LOGGER.debug("Could not load outlet names for buttons: %s", e)

    entities: list[ButtonEntity] = []

    # Per-outlet reset buttons
    for i in range(outlets):
        n = i + 1
        if i < len(names) and names[i]:
            label = f"{n} - {names[i]} Reset"
        else:
            label = f"WattBox Outlet {n} Reset"
        entities.append(WBResetButton(client, entry, n, label))

    # Reset all button (outlet=0)
    entities.append(WBResetAllButton(client, entry, "WattBox Reset All"))

    add_entities(entities, True)


class WBBase(ButtonEntity):
    """Base for WattBox buttons"""

    def __init__(self, client: WattBoxHTTPClient, entry: ConfigEntry, name: str, unique_suffix: str):
        self._client = client
        self._entry = entry
        self._attr_name = name
        self._attr_unique_id = f"wb_300_700_{entry.data.get('host')}_{unique_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
            "name": f"WattBox 300/700 ({entry.data.get('host')})",
            "manufacturer": "Snap One",
            "model": entry.data.get(CONF_MODEL, DEFAULT_MODEL),
        }


class WBResetButton(WBBase):
    """Reset one outlet"""

    def __init__(self, client: WattBoxHTTPClient, entry: ConfigEntry, outlet: int, label: str):
        super().__init__(client, entry, label, f"outlet_{outlet}_reset")
        self._outlet = outlet

    async def async_press(self) -> None:
        await self._client.reset_outlet(self._outlet)


class WBResetAllButton(WBBase):
    """Reset all outlets"""

    def __init__(self, client: WattBoxHTTPClient, entry: ConfigEntry, label: str):
        super().__init__(client, entry, label, "reset_all")

    async def async_press(self) -> None:
        await self._client.reset_outlet(0)
