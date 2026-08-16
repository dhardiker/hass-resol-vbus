"""Binary sensors (relays and option flags) for RESOL VBus/LAN."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .fields import DEVICE_MODEL, FIELDS


def _is_bitfield(field) -> bool:
    return len(field["parts"]) == 1 and field["parts"][0][1] not in (255,)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    data = hass.data[DOMAIN]
    coordinator = data["coordinator"]
    conf = data["config"]
    async_add_entities(
        ResolBinarySensor(coordinator, conf, field)
        for field in FIELDS
        if _is_bitfield(field)
    )


class ResolBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, conf, field) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = conf["names"].get(field["id"], field["name"])
        self._attr_unique_id = f"resol_vbus_{conf['host']}_{field['id']}"
        is_option = field["name"].startswith("Option:")
        if is_option:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False
        else:  # relays drive pumps/valves
            self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_device_info = {
            "identifiers": {(DOMAIN, conf["host"])},
            "name": conf["name"],
            "manufacturer": "RESOL",
            "model": f"{DEVICE_MODEL} via VBus/LAN",
        }

    @property
    def is_on(self):
        value = (self.coordinator.data or {}).get(self._field["id"])
        return None if value is None else bool(value)
