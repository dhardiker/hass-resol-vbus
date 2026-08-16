"""Sensors for the RESOL VBus/LAN integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .fields import DEVICE_MODEL, FIELDS

# Temperature inputs with no probe attached read this sentinel.
SENTINEL_MIN = 888.0

# unit -> (device_class, state_class, category, enabled_default)
_META = {
    "°C": (SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, None, True),
    "m³/h": (SensorDeviceClass.VOLUME_FLOW_RATE, SensorStateClass.MEASUREMENT, None, True),
    "W/m²": (SensorDeviceClass.IRRADIANCE, SensorStateClass.MEASUREMENT, None, True),
    "%": (None, SensorStateClass.MEASUREMENT, None, True),
    "h": (SensorDeviceClass.DURATION, SensorStateClass.TOTAL_INCREASING, None, True),
    "Wh": (SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, True),
}

# Bitfields become binary_sensors; these numeric oddments stay sensors
# but as disabled-by-default diagnostics.
_DIAGNOSTIC_IDS = {"024_2_0", "026_1_0"}  # System time, Scheme


def _is_bitfield(field) -> bool:
    return len(field["parts"]) == 1 and field["parts"][0][1] not in (255,)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    data = hass.data[DOMAIN]
    coordinator = data["coordinator"]
    conf = data["config"]
    entities = [
        ResolSensor(coordinator, conf, field)
        for field in FIELDS
        if not _is_bitfield(field)
    ]
    async_add_entities(entities)


class ResolSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, conf, field) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = conf["names"].get(field["id"], field["name"])
        self._attr_unique_id = f"resol_vbus_{conf['host']}_{field['id']}"
        unit = field["unit"] or None
        self._attr_native_unit_of_measurement = unit
        device_class, state_class, category, enabled = _META.get(
            unit, (None, None, None, True)
        )
        if field["id"] in _DIAGNOSTIC_IDS:
            category, enabled = EntityCategory.DIAGNOSTIC, False
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_entity_category = category
        self._attr_entity_registry_enabled_default = enabled
        self._attr_suggested_display_precision = field["precision"]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, conf["host"])},
            "name": conf["name"],
            "manufacturer": "RESOL",
            "model": f"{DEVICE_MODEL} via VBus/LAN",
            "configuration_url": f"http://{conf['host']}/",
        }

    @property
    def native_value(self):
        value = (self.coordinator.data or {}).get(self._field["id"])
        if value is None:
            return None
        if (
            self._attr_device_class == SensorDeviceClass.TEMPERATURE
            and value >= SENTINEL_MIN
        ):
            return None  # probe not connected
        return value
