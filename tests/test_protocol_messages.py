import unittest

from twcmanager.protocol.messages import (
    build_twc_frame,
    parse_twc_frame,
    extract_frames,
    slip_escape,
    slip_unescape,
)


class TestProtocolMessages(unittest.TestCase):
    def test_escape_unescape_roundtrip(self):
        payload = bytes([0xFB, 0xE0, 0xC0, 0xDB, 0x01])
        self.assertEqual(slip_unescape(slip_escape(payload)), payload)

    def test_build_and_parse_frame_checksum(self):
        msg = bytes([0xFB, 0xE0, 0x11, 0x22, 0x33])
        frame = build_twc_frame(msg)
        parsed = parse_twc_frame(frame)
        self.assertTrue(parsed.checksum_ok)
        self.assertEqual(parsed.payload, msg)

    def test_extract_frames_from_stream(self):
        msg1 = build_twc_frame(bytes([0xFB, 0xE0, 0x01]))
        msg2 = build_twc_frame(bytes([0xFB, 0xE2, 0x02]))
        buf = bytearray(b"\x00\x01" + msg1 + msg2[:4])

        frames = extract_frames(buf)
        self.assertEqual(len(frames), 1)
        self.assertGreater(len(buf), 0)

        buf.extend(msg2[4:])
        frames2 = extract_frames(buf)
        self.assertEqual(len(frames2), 1)


if __name__ == "__main__":
    unittest.main()
