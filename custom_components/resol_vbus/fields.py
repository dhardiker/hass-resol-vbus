"""Field decode table for the RESOL DeltaSol ES broadcast packet
(dst 0x0010, src 0x7411, cmd 0x0100).

Generated 2026-08-16 from the resol-vbus JS library's canonical VSF
specification (Specification.getPacketSpecification). Do not hand-edit
values; regenerate from the library if the controller changes."""

PACKET_SOURCE = 0x7411
PACKET_DEST = 0x0010
PACKET_COMMAND = 0x0100
DEVICE_MODEL = "DeltaSol ES"

# Each part: (offset, mask, bit_pos, is_signed, factor)
FIELDS = [
    {"id": "000_2_0", "name": "Temperature sensor 1", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(0, 255, 0, False, 1), (1, 255, 0, True, 256)]},
    {"id": "002_2_0", "name": "Temperature sensor 2", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(2, 255, 0, False, 1), (3, 255, 0, True, 256)]},
    {"id": "004_2_0", "name": "Temperature sensor 3", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(4, 255, 0, False, 1), (5, 255, 0, True, 256)]},
    {"id": "006_2_0", "name": "Temperature sensor 4", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(6, 255, 0, False, 1), (7, 255, 0, True, 256)]},
    {"id": "008_2_0", "name": "Temperature sensor 5", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(8, 255, 0, False, 1), (9, 255, 0, True, 256)]},
    {"id": "010_2_0", "name": "Temperature sensor 6", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(10, 255, 0, False, 1), (11, 255, 0, True, 256)]},
    {"id": "012_2_0", "name": "Temperature sensor 7", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(12, 255, 0, False, 1), (13, 255, 0, True, 256)]},
    {"id": "014_2_0", "name": "Temperature sensor 8", "factor": 0.1, "unit": "\u00b0C", "precision": 1, "parts": [(14, 255, 0, False, 1), (15, 255, 0, True, 256)]},
    {"id": "016_2_0", "name": "Flow rate", "factor": 0.01, "unit": "m\u00b3/h", "precision": 2, "parts": [(16, 255, 0, False, 1), (17, 255, 0, True, 256)]},
    {"id": "018_2_0", "name": "Irradiation", "factor": 1, "unit": "W/m\u00b2", "precision": 0, "parts": [(18, 255, 0, False, 1), (19, 255, 0, True, 256)]},
    {"id": "021_1_0", "name": "Pump speed 1", "factor": 1, "unit": "%", "precision": 0, "parts": [(21, 255, 0, False, 1)]},
    {"id": "022_1_0", "name": "Pump speed 2", "factor": 1, "unit": "%", "precision": 0, "parts": [(22, 255, 0, False, 1)]},
    {"id": "023_1_0", "name": "Pump speed 3", "factor": 1, "unit": "%", "precision": 0, "parts": [(23, 255, 0, False, 1)]},
    {"id": "020_1_8", "name": "Relay 4", "factor": 1, "unit": "", "precision": 0, "parts": [(20, 8, 3, True, 1)]},
    {"id": "020_1_16", "name": "Relay 5", "factor": 1, "unit": "", "precision": 0, "parts": [(20, 16, 4, True, 1)]},
    {"id": "020_1_32", "name": "Relay 6", "factor": 1, "unit": "", "precision": 0, "parts": [(20, 32, 5, True, 1)]},
    {"id": "024_2_0", "name": "System time", "factor": 1, "unit": "", "precision": 0, "parts": [(24, 255, 0, False, 1), (25, 255, 0, True, 256)]},
    {"id": "026_1_0", "name": "Scheme", "factor": 1, "unit": "", "precision": 0, "parts": [(26, 255, 0, False, 1)]},
    {"id": "027_1_1", "name": "Option: collector cooling", "factor": 1, "unit": "", "precision": 0, "parts": [(27, 1, 0, True, 1)]},
    {"id": "027_1_2", "name": "Option: collector minimum limitation", "factor": 1, "unit": "", "precision": 0, "parts": [(27, 2, 1, True, 1)]},
    {"id": "027_1_4", "name": "Option: Frost protection function", "factor": 1, "unit": "", "precision": 0, "parts": [(27, 4, 2, True, 1)]},
    {"id": "027_1_8", "name": "Option: tube collector function", "factor": 1, "unit": "", "precision": 0, "parts": [(27, 8, 3, True, 1)]},
    {"id": "027_1_16", "name": "Option: recooling", "factor": 1, "unit": "", "precision": 0, "parts": [(27, 16, 4, True, 1)]},
    {"id": "027_1_32", "name": "Option: heat quantity measurement", "factor": 1, "unit": "", "precision": 0, "parts": [(27, 32, 5, True, 1)]},
    {"id": "028_2_0", "name": "Operating hours 1", "factor": 1, "unit": "h", "precision": 0, "parts": [(28, 255, 0, False, 1), (29, 255, 0, False, 256)]},
    {"id": "030_2_0", "name": "Operating hours 2", "factor": 1, "unit": "h", "precision": 0, "parts": [(30, 255, 0, False, 1), (31, 255, 0, False, 256)]},
    {"id": "032_2_0", "name": "Operating hours 3", "factor": 1, "unit": "h", "precision": 0, "parts": [(32, 255, 0, False, 1), (33, 255, 0, False, 256)]},
    {"id": "034_2_0", "name": "Operating hours 4", "factor": 1, "unit": "h", "precision": 0, "parts": [(34, 255, 0, False, 1), (35, 255, 0, False, 256)]},
    {"id": "036_2_0", "name": "Operating hours 5", "factor": 1, "unit": "h", "precision": 0, "parts": [(36, 255, 0, False, 1), (37, 255, 0, False, 256)]},
    {"id": "038_2_0", "name": "Operating hours 6", "factor": 1, "unit": "h", "precision": 0, "parts": [(38, 255, 0, False, 1), (39, 255, 0, False, 256)]},
    {"id": "040_2_0", "name": "Heat quantity", "factor": 1, "unit": "Wh", "precision": 0, "parts": [(40, 255, 0, False, 1), (41, 255, 0, False, 256), (42, 255, 0, False, 1000), (43, 255, 0, False, 256000), (44, 255, 0, False, 1000000), (45, 255, 0, False, 256000000)]},
]
