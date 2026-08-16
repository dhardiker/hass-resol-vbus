"""Diagnostics for RESOL VBus/LAN.

Downloadable from Settings → Devices → (the device) → Download
diagnostics. Designed so a bug report answers "which layer failed":

- ``connect_attempts`` high + ``bytes_received`` 0 → network/login
  (wrong host, wrong password, or another client holds the adapter's
  single data connection).
- bytes flowing but ``packets_decoded`` 0 → framing/checksum (wrong
  device? noise?); the checksum-failure counters say which.
- packets decoded but ``packet_age_s`` large → the adapter stopped
  relaying the bus (controller off? VBus wiring?).
- ``last_raw_packet_hex`` lets a maintainer replay a user's exact
  packet through the test suite.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from . import DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry):
    return _diagnostics(hass)


async def async_get_device_diagnostics(hass: HomeAssistant, entry, device):
    return _diagnostics(hass)


def _diagnostics(hass: HomeAssistant) -> dict:
    data = hass.data.get(DOMAIN, {})
    client = data.get("client")
    conf = dict(data.get("config", {}))
    conf.pop("password", None)
    if client is None:
        return {"error": "integration not set up"}
    return {
        "config": conf,
        "connected": client.connected,
        "packet_age_s": round(client.age_s, 1) if client.data else None,
        "stats": client.stats,
        "decoded_fields": client.data,
        "last_raw_packet_hex": client.last_raw_packet_hex,
    }
