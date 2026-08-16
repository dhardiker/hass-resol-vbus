"""Minimal VBus-over-TCP client for a RESOL VBus/LAN adapter.

Speaks the adapter's line-based login protocol (+HELLO / PASS / DATA),
then parses the raw VBus 1.0 stream: sync 0xAA, 8-byte header +
checksum, then frames of 4 payload bytes + septet byte + checksum.
Checksum and septet algorithms mirror resol-vbus's header.js
(calcChecksumV0, injectSeptett) exactly.

Only the one broadcast packet this integration cares about is
assembled; everything else on the bus is skipped cheaply.
"""
from __future__ import annotations

import asyncio
import logging
import time

from .fields import FIELDS, PACKET_COMMAND, PACKET_DEST, PACKET_SOURCE

_LOGGER = logging.getLogger(__name__)

RECONNECT_DELAY_S = 10
HANDSHAKE_TIMEOUT_S = 10


def _checksum_v0(buf: bytes) -> int:
    return (0x7F - (sum(buf) & 0x7F)) & 0x7F


def _inject_septett(frame: bytes) -> bytes:
    """frame = 4 payload bytes + septet byte; returns 4 real bytes."""
    septett = frame[4]
    return bytes(
        b | 0x80 if septett & (1 << i) else b for i, b in enumerate(frame[:4])
    )


def decode_fields(payload: bytes) -> dict[str, float]:
    """Decode the packet payload into {field_id: engineering value}."""
    values: dict[str, float] = {}
    for field in FIELDS:
        raw = 0
        ok = True
        for offset, mask, bit_pos, is_signed, factor in field["parts"]:
            if offset >= len(payload):
                ok = False
                break
            part = payload[offset] & mask
            if bit_pos:
                part >>= bit_pos
            if is_signed and part & 0x80:
                part -= 0x100
            raw += part * factor
        if ok:
            values[field["id"]] = raw * field["factor"]
    return values


class VBusClient:
    """Maintains the adapter connection and the latest decoded packet."""

    def __init__(self, host: str, password: str, port: int = 7053) -> None:
        self._host = host
        self._port = port
        self._password = password
        self._task: asyncio.Task | None = None
        self.data: dict[str, float] = {}
        self.last_packet_monotonic: float = 0.0
        self.connected: bool = False
        # Debug/diagnostic counters — surfaced via the diagnostics platform
        # so a misbehaving install can show exactly which layer is failing:
        # no bytes = network/login; bytes but no packets = framing/checksum;
        # packets but stale data = the adapter stopped relaying the bus.
        self.stats: dict[str, int | str | None] = {
            "connect_attempts": 0,
            "bytes_received": 0,
            "packets_decoded": 0,
            "header_checksum_failures": 0,
            "frame_checksum_failures": 0,
            "foreign_packets_skipped": 0,
            "last_error": None,
        }
        self.last_raw_packet_hex: str | None = None

    @property
    def age_s(self) -> float:
        if not self.last_packet_monotonic:
            return float("inf")
        return time.monotonic() - self.last_packet_monotonic

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.get_event_loop().create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self.connected = False

    async def _run(self) -> None:
        while True:
            try:
                await self._connect_and_stream()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 - keep the loop alive
                self.stats["last_error"] = f"{type(err).__name__}: {err}"
                _LOGGER.warning(
                    "VBus connection to %s lost/failed (%s); retrying in %ss",
                    self._host, err, RECONNECT_DELAY_S,
                )
            self.connected = False
            await asyncio.sleep(RECONNECT_DELAY_S)

    async def _connect_and_stream(self) -> None:
        self.stats["connect_attempts"] += 1
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self._host, self._port), HANDSHAKE_TIMEOUT_S
        )
        try:
            async def expect_ok(context: str) -> None:
                line = await asyncio.wait_for(reader.readline(), HANDSHAKE_TIMEOUT_S)
                if not line.startswith(b"+"):
                    raise ConnectionError(f"{context}: adapter said {line!r}")

            await expect_ok("greeting")  # +HELLO
            writer.write(f"PASS {self._password}\r\n".encode())
            await writer.drain()
            await expect_ok("PASS")
            writer.write(b"DATA\r\n")
            await writer.drain()
            await expect_ok("DATA")
            _LOGGER.info("VBus stream open from %s", self._host)
            self.connected = True

            buf = bytearray()
            while True:
                chunk = await asyncio.wait_for(reader.read(1024), 60)
                if not chunk:
                    raise ConnectionError("stream closed by adapter")
                self.stats["bytes_received"] += len(chunk)
                buf += chunk
                self._extract_packets(buf)
                if len(buf) > 4096:  # never let garbage grow unbounded
                    del buf[:-512]
        finally:
            writer.close()

    def _extract_packets(self, buf: bytearray) -> None:
        while True:
            try:
                start = buf.index(0xAA)
            except ValueError:
                buf.clear()
                return
            if start:
                del buf[:start]
            if len(buf) < 10:
                return  # need sync + 8 header bytes + checksum
            header = bytes(buf[1:9])
            if _checksum_v0(header) != buf[9]:
                self.stats["header_checksum_failures"] += 1
                del buf[:1]  # false sync; resync from next byte
                continue
            dst = header[0] | header[1] << 8
            src = header[2] | header[3] << 8
            proto = header[4]
            if proto != 0x10:
                # Not a 1.0 packet (datagram etc.) — skip past this sync.
                del buf[:1]
                continue
            cmd = header[5] | header[6] << 8
            frame_count = header[7]
            total = 10 + frame_count * 6
            if len(buf) < total:
                return  # wait for the rest
            if (dst, src, cmd) == (PACKET_DEST, PACKET_SOURCE, PACKET_COMMAND):
                payload = bytearray()
                good = True
                for i in range(frame_count):
                    frame = bytes(buf[10 + i * 6 : 10 + i * 6 + 6])
                    if _checksum_v0(frame[:5]) != frame[5]:
                        self.stats["frame_checksum_failures"] += 1
                        good = False
                        break
                    payload += _inject_septett(frame)
                if good:
                    self.data = decode_fields(bytes(payload))
                    self.last_packet_monotonic = time.monotonic()
                    self.stats["packets_decoded"] += 1
                    self.last_raw_packet_hex = bytes(buf[:total]).hex()
                    if self.stats["packets_decoded"] == 1:
                        _LOGGER.info(
                            "first packet decoded from %s (%d fields)",
                            self._host, len(self.data),
                        )
            else:
                self.stats["foreign_packets_skipped"] += 1
            del buf[:total]
