"""RESOL VBus/LAN integration: native entities from the raw VBus stream.

Born 2026-08-16 to replace the smart-red-house-resol-vbus docker
container + MQTT + Node-RED chain. The off-the-shelf Resol integrations
need a KM2's HTTP API; this speaks raw VBus-over-TCP to a bare VBus/LAN
adapter instead. YAML-configured for now; a config flow can come with
HACS-ification.
"""
from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .vbus import VBusClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "resol_vbus"
CONF_NAMES = "names"
DEFAULT_NAME = "Solar (RESOL DeltaSol ES)"

# A packet normally arrives every second; if none for this long the
# entities go unavailable rather than freezing at the last value.
STALE_AFTER_S = 120

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PASSWORD, default="vbus"): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=10): cv.positive_int,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_NAMES, default={}): {cv.string: cv.string},
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config) -> bool:
    conf = config[DOMAIN]
    client = VBusClient(conf[CONF_HOST], conf[CONF_PASSWORD])
    client.start()

    async def _async_update():
        # The client streams continuously; this just snapshots it on the
        # coordinator's cadence so entities update at a sane rate.
        if client.age_s > STALE_AFTER_S:
            raise UpdateFailed(f"no VBus packet for {client.age_s:.0f}s")
        return dict(client.data)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update,
        update_interval=timedelta(seconds=conf[CONF_SCAN_INTERVAL]),
    )

    hass.data[DOMAIN] = {
        "client": client,
        "coordinator": coordinator,
        "config": conf,
    }

    async def _stop(_event) -> None:
        await client.stop()

    hass.bus.async_listen_once("homeassistant_stop", _stop)

    await coordinator.async_refresh()
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    hass.async_create_task(
        async_load_platform(hass, "binary_sensor", DOMAIN, {}, config)
    )
    return True
