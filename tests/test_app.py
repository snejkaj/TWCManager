import unittest

from twcmanager.app import TWCManagerApp, SlaveState
from twcmanager.config import Settings
from twcmanager.providers.base import MeterReading, PowerMeterProvider
from twcmanager.protocol.messages import build_twc_frame
from twcmanager.protocol.transport import TwcTransport


class StaticMeter(PowerMeterProvider):
    def __init__(self, reading: MeterReading):
        self.reading = reading

    def get_reading(self) -> MeterReading:
        return self.reading


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


class TestApp(unittest.TestCase):
    def test_distribution(self):
        app = TWCManagerApp(settings=Settings(main_fuse_amps=25, min_amps_per_twc=6))
        app.slaves = {"1": SlaveState("1"), "2": SlaveState("2")}
        app.meter = StaticMeter(MeterReading(grid_power_w=2300, voltage_v=230))

        _, target = app.tick()
        self.assertEqual(target, 13.0)
        self.assertEqual(app.slaves["1"].amps_offered + app.slaves["2"].amps_offered, 13.0)

    def test_handle_protocol_payload_updates_slave(self):
        app = TWCManagerApp(settings=Settings())
        linkready = b"\xFD\xE2\x12\x34\x77\x0C\x80\x00\x00"
        app.handle_protocol_payload(linkready)
        self.assertIn("1234", app.slaves)

        heartbeat = b"\xFD\xE0\x12\x34\x77\x77\x05\x0C\x80\x05\xDC\x00\x00\x00\x00"
        app.handle_protocol_payload(heartbeat)
        self.assertAlmostEqual(app.slaves["1234"].amps_actual, 15.0, places=2)

    def test_process_protocol_once_reads_and_writes_heartbeat(self):
        incoming = build_twc_frame(b"\xFD\xE2\x12\x34\x77\x0C\x80\x00\x00")
        serial = FakeSerial(read_bytes=incoming)
        app = TWCManagerApp(settings=Settings(fake_twc_id_hex="7777"))
        app.transport = TwcTransport(serial)

        app.slaves["1234"] = SlaveState("1234", amps_actual=0.0, amps_offered=10.0)
        count = app.process_protocol_once()

        self.assertEqual(count, 1)
        self.assertGreater(len(serial.written), 0)


if __name__ == "__main__":
    unittest.main()
