"""Sensors for the RESOL VBus/LAN integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfInformation, UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .fields import DEVICE_MODEL, FIELDS
from .vbus import STAT_COUNTERS

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
    client = data["client"]
    entities += [ResolLinkCounter(client, conf, key) for key in STAT_COUNTERS]
    entities += [ResolPacketAge(client, conf), ResolLastError(client, conf)]
    async_add_entities(entities, update_before_add=True)


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


def _device_info(conf):
    return {
        "identifiers": {(DOMAIN, conf["host"])},
        "name": conf["name"],
        "manufacturer": "RESOL",
        "model": f"{DEVICE_MODEL} via VBus/LAN",
        "configuration_url": f"http://{conf['host']}/",
    }


class _ResolLinkEntity(SensorEntity):
    """Link-health entities read the client directly and stay available
    through an outage, which is when they matter. Polled by HA (30 s)
    rather than tied to the coordinator, whose failure marks its
    entities unavailable."""

    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_available = True

    def __init__(self, client, conf, key: str, name: str) -> None:
        self._client = client
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"resol_vbus_{conf['host']}_link_{key}"
        self._attr_device_info = _device_info(conf)


class ResolLinkCounter(_ResolLinkEntity):
    """One of VBusClient.stats' integer counters. Counts since HA last
    started; total_increasing lets long-term statistics bridge restarts."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, client, conf, key: str) -> None:
        super().__init__(client, conf, key, "VBus " + key.replace("_", " "))
        if key == "bytes_received":
            self._attr_device_class = SensorDeviceClass.DATA_SIZE
            self._attr_native_unit_of_measurement = UnitOfInformation.BYTES

    @property
    def native_value(self):
        return self._client.stats.get(self._key)


class ResolPacketAge(_ResolLinkEntity):
    """Seconds since the last decoded packet (normally about one)."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_display_precision = 0

    def __init__(self, client, conf) -> None:
        super().__init__(client, conf, "packet_age", "VBus packet age")

    @property
    def native_value(self):
        age = self._client.age_s
        return None if age == float("inf") else round(age, 1)


class ResolLastError(_ResolLinkEntity):
    """The last connection error the client saw, as text ("none" when clear)."""

    def __init__(self, client, conf) -> None:
        super().__init__(client, conf, "last_error", "VBus last error")

    @property
    def native_value(self):
        err = self._client.stats.get("last_error")
        return str(err)[:255] if err else "none"

