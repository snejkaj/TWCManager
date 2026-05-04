import unittest

from twcmanager.protocol.messages import build_twc_frame
from twcmanager.protocol.transport import TwcTransport


class FakeSerial:
    def __init__(self, read_bytes: bytes = b""):
        self._buf = bytearray(read_bytes)
        self.written = bytearray()

    @property
    def in_waiting(self):
        return len(self._buf)

    def read(self, n: int):
        out = self._buf[:n]
        del self._buf[:n]
        return bytes(out)

    def write(self, data: bytes):
        self.written.extend(data)


class TestTwcTransport(unittest.TestCase):
    def test_send_payload(self):
        fake = FakeSerial()
        t = TwcTransport(fake)
        payload = bytes([0xFB, 0xE0, 0x01, 0x02])
        t.send_payload(payload)
        self.assertEqual(bytes(fake.written), build_twc_frame(payload))

    def test_poll_filters_bad_checksum(self):
        good = build_twc_frame(bytes([0xFB, 0xE0, 0x01]))
        bad = bytearray(build_twc_frame(bytes([0xFB, 0xE2, 0x02])))
        bad[-2] ^= 0xFF

        fake = FakeSerial(read_bytes=good + bytes(bad))
        t = TwcTransport(fake)
        payloads = t.poll()

        self.assertEqual(payloads, [bytes([0xFB, 0xE0, 0x01])])


if __name__ == "__main__":
    unittest.main()
