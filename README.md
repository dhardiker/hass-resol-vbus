# RESOL VBus/LAN for Home Assistant

Native Home Assistant integration for RESOL solar/heating controllers
reached through a bare **VBus/LAN Adapter** — the device the existing
community integrations *can't* talk to.

The excellent [KM2 integrations](https://github.com/dm82m/hass-Deltasol-KM2)
poll a JSON/HTTP API that only KM1/KM2/DL2/DL3 gateways provide. A plain
VBus/LAN Adapter has no data API at all: just the raw VBus protocol on
TCP port 7053. This integration speaks that protocol directly — no
MQTT, no bridge container, no cloud — and creates a proper HA device
with sensors that carry the right `device_class`/`state_class`, so
temperatures chart natively and operating hours / heat quantity flow
into HA's long-term statistics.

Currently decodes the **DeltaSol ES** broadcast packet (31 fields:
8 temperature inputs, pump speeds, relays, operating hours, heat
quantity, flow, irradiation, option flags). The decode table is
machine-generated from the canonical
[resol-vbus](https://github.com/danielwippermann/resol-vbus) VSF
specification, so extending to other controllers is a regeneration, not
a reverse-engineering effort — see *Adding your controller* below.

## Install

**HACS (custom repository):** HACS → Integrations → ⋮ → Custom
repositories → add this repo URL, category *Integration* → install →
restart HA.

**Manual:** copy `custom_components/resol_vbus/` into your `config/`
and restart.

## Configure

YAML for now (config flow is on the roadmap):

```yaml
resol_vbus:
  host: 192.168.1.50          # your VBus/LAN adapter
  password: !secret vbus_password   # adapter password, default "vbus"
  scan_interval: 10           # seconds between entity updates
  name: Solar (RESOL DeltaSol ES)
  names:                      # optional friendly names per field id
    "000_2_0": Solar Roof
    "002_2_0": Solar Hot Water Bottom
    "004_2_0": Solar Hot Water Top
    "006_2_0": Solar Pool
```

Field ids are the offset/size/bit-position triplets from the VBus
specification — run with defaults first and the entity names show which
is which.

Notes:

- The adapter accepts **one** data connection. Stop any other VBus
  client (RSC, a resol-vbus JSON server, etc.) before starting HA, or
  the integration will log connection resets and retry every 10s.
- Temperature inputs with no probe read a `888.8` sentinel; those
  entities show as unknown rather than as a very hot roof.
- Everything is read-only. VBus parameterization (writing to the
  controller) is deliberately out of scope.

## Debugging

The integration is built to tell you *which layer* is broken:

1. **Device page → Download diagnostics.** The counters localize the
   fault: no bytes received → network/login/another-client; bytes but
   no packets → framing (the checksum-failure counters say more);
   packets but stale → the controller side of the adapter.
2. The diagnostics include `last_raw_packet_hex` — a maintainer can
   replay your exact packet through the test suite.
3. `logger:` at `debug` for `custom_components.resol_vbus` narrates
   connection lifecycle.

## Development

```sh
python3 -m pytest tests/
```

The protocol layer (`vbus.py`, `fields.py`) is deliberately HA-free and
tested against `tests/fixtures/live_stream.hex` — raw bytes captured
from a real adapter. The tests exercise checksum, septet reinjection,
framing, resync-after-garbage, incremental feeding, and corrupt-frame
rejection against that live capture.

### Adding your controller

`fields.py` is generated from the resol-vbus JS library:

```js
const spec = Specification.getDefaultSpecification();
const ps = spec.getPacketSpecification("<channel>_<dst>_<src>_10_<cmd>");
// serialize ps.packetFields — see the header of fields.py
```

Substitute your controller's source address (visible in the packet
stream or in the resol-vbus documentation), regenerate, and open a PR —
multi-packet support is the intended growth path.

## Credits

Protocol semantics (checksum, septet handling, field specifications)
derive from Daniel Wippermann's
[resol-vbus](https://github.com/danielwippermann/resol-vbus) library —
the canonical VBus implementation. This project reimplements the small
read-only subset needed for a Home Assistant integration.

## License

MIT — see [LICENSE](LICENSE).
