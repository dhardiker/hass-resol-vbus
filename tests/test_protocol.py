"""Protocol tests against a captured live stream from a real VBus/LAN
adapter fronting a DeltaSol ES (2026-08-16). The fixture is raw wire
bytes; if these tests pass, the checksum, septet, framing, resync, and
field-decode layers all agree with reality, not just with each other."""


def _client(vbus_mod):
    return vbus_mod.VBusClient("test-host", "test-pass")


def test_checksum_known_answer(vbus_mod):
    # 0x7F minus the 7-bit sum, per resol-vbus header.js calcChecksumV0.
    assert vbus_mod._checksum_v0(b"\x00") == 0x7F
    assert vbus_mod._checksum_v0(b"\x01\x02\x03") == 0x79
    assert vbus_mod._checksum_v0(b"\x7f\x7f") == 0x01


def test_septett_reinjection(vbus_mod):
    # Frame carries 4 bytes stripped of MSBs + a septet byte holding them.
    frame = bytes([0x01, 0x02, 0x03, 0x04, 0b0101])
    assert vbus_mod._inject_septett(frame) == bytes([0x81, 0x02, 0x83, 0x04])


def test_live_stream_decodes(vbus_mod, live_stream):
    client = _client(vbus_mod)
    buf = bytearray(live_stream)
    client._extract_packets(buf)
    assert client.stats["packets_decoded"] >= 1
    data = client.data
    assert len(data) == 31
    # Wired temperature probes: plausible plant values.
    for fid in ("000_2_0", "002_2_0", "004_2_0", "006_2_0"):
        assert -30 < data[fid] < 120, f"{fid} implausible: {data[fid]}"
    # Unwired probes read the 888.8 sentinel (raw 8888 x 0.1).
    for fid in ("008_2_0", "010_2_0", "012_2_0", "014_2_0"):
        assert round(data[fid], 1) == 888.8
    # Bitfields decode to clean booleans-as-numbers.
    for fid in ("020_1_8", "020_1_16", "020_1_32"):
        assert data[fid] in (0, 1)
    # Operating hours are plausibly large monotonic counters.
    assert data["028_2_0"] > 1000


def test_resync_after_garbage(vbus_mod, live_stream):
    client = _client(vbus_mod)
    buf = bytearray(b"\x12\x34\xaa\x99" + live_stream)  # noise + false sync
    client._extract_packets(buf)
    assert client.stats["packets_decoded"] >= 1


def test_truncated_packet_waits_for_more(vbus_mod, live_stream):
    client = _client(vbus_mod)
    start = live_stream.index(0xAA)
    buf = bytearray(live_stream[start : start + 20])  # header + partial frames
    client._extract_packets(buf)
    assert client.stats["packets_decoded"] == 0
    assert len(buf) > 0  # kept, awaiting the rest


def test_incremental_feed_matches_bulk(vbus_mod, live_stream):
    bulk = _client(vbus_mod)
    bulk._extract_packets(bytearray(live_stream))

    drip = _client(vbus_mod)
    buf = bytearray()
    for i in range(0, len(live_stream), 7):  # awkward chunk size on purpose
        buf += live_stream[i : i + 7]
        drip._extract_packets(buf)
    assert drip.stats["packets_decoded"] == bulk.stats["packets_decoded"]
    assert drip.data == bulk.data


def test_corrupt_frame_rejected(vbus_mod, live_stream):
    # Find OUR packet's header on the wire (the stream also carries
    # datagrams): sync, dst 0x0010 LE, src 0x7411 LE, protocol 0x10.
    signature = bytes([0xAA, 0x10, 0x00, 0x11, 0x74, 0x10])
    start = live_stream.index(signature)
    client = _client(vbus_mod)
    packet = bytearray(live_stream[start:])
    packet[11] ^= 0x01  # flip a data bit inside the first frame
    client._extract_packets(packet)
    assert client.stats["frame_checksum_failures"] >= 1


def test_field_table_shape(fields_mod):
    assert len(fields_mod.FIELDS) == 31
    ids = [f["id"] for f in fields_mod.FIELDS]
    assert len(ids) == len(set(ids)), "duplicate field ids"
    for f in fields_mod.FIELDS:
        assert f["parts"], f"{f['id']} has no parts"
        for offset, mask, bit_pos, _signed, factor in f["parts"]:
            assert 0 <= offset < 64
            assert 0 < mask <= 255
            assert factor != 0
