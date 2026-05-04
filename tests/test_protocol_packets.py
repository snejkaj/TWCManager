import unittest

from twcmanager.protocol.packets import (
    build_master_heartbeat,
    build_master_linkready2,
    encode_amps,
    decode_amps,
    parse_linkready,
    parse_slave_heartbeat,
)


class TestProtocolPackets(unittest.TestCase):
    def test_encode_decode_amps(self):
        self.assertEqual(decode_amps(encode_amps(12.34)), 12.34)

    def test_parse_linkready(self):
        payload = b"\xFD\xE2\x12\x34\x77" + encode_amps(32.0) + b"\x00\x00"
        lr = parse_linkready(payload)
        self.assertIsNotNone(lr)
        self.assertEqual(lr.sender_id, b"\x12\x34")
        self.assertEqual(lr.max_amps, 32.0)

    def test_parse_slave_heartbeat(self):
        hb = b"\xFD\xE0\x12\x34\x77\x77" + b"\x05" + encode_amps(16.0) + encode_amps(10.5) + b"\x00\x00\x00\x00"
        parsed = parse_slave_heartbeat(hb)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.status, 0x05)
        self.assertEqual(parsed.amps_max, 16.0)
        self.assertEqual(parsed.amps_actual, 10.5)

    def test_build_master_payloads(self):
        mh = build_master_heartbeat(b"\x77\x77", b"\x12\x34", 13.0)
        self.assertTrue(mh.startswith(b"\xFB\xE0\x77\x77\x12\x34"))

        lr2 = build_master_linkready2(b"\x77\x77")
        self.assertTrue(lr2.startswith(b"\xFB\xE2\x77\x77"))


if __name__ == "__main__":
    unittest.main()
