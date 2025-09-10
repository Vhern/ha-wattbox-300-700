from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .api import WattBoxHTTPClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities: AddEntitiesCallback) -> None:
    client: WattBoxHTTPClient = hass.data[DOMAIN][entry.entry_id]["client"]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    async def _update() -> dict[str, Optional[float]]:
        try:
            return await client.get_metrics()
        except Exception as e:
            _LOGGER.warning("WattBox metrics poll failed: %s", e)
            raise UpdateFailed(str(e)) from e

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattbox_300_700_sensor",
        update_method=_update,
        update_interval=timedelta(seconds=scan_interval),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        _LOGGER.warning("Initial metrics refresh failed, continuing: %s", e)
        coordinator.async_set_updated_data({"voltage": None, "current": None, "power": None})

    add_entities(
        [
            WBMetricSensor(coordinator, entry, "Voltage", "voltage", "V"),
            WBMetricSensor(coordinator, entry, "Current", "current", "A"),
            WBMetricSensor(coordinator, entry, "Power", "power", "W"),
        ],
        True,
    )


class WBMetricSensor(SensorEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry, name: str, key: str, unit: str):
        self.coordinator = coordinator
        self._entry = entry
        self._key = key
        self._attr_name = f"WattBox {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"wb_300_700_{entry.data.get('host')}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data.get("host"))},
            "name": f"WattBox 300/700 ({entry.data.get('host')})",
            "manufacturer": "Snap One",
            "model": "WattBox 300/700",
        }

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return data.get(self._key)

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
