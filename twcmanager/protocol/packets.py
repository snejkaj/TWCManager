from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LinkReady:
    sender_id: bytes
    sign: int
    max_amps: float


@dataclass
class Heartbeat:
    sender_id: bytes
    receiver_id: bytes
    status: int
    amps_max: float
    amps_actual: float
    raw: bytes


def encode_amps(amps: float) -> bytes:
    val = int(round(amps * 100))
    return bytes([(val >> 8) & 0xFF, val & 0xFF])


def decode_amps(two_bytes: bytes) -> float:
    return ((two_bytes[0] << 8) + two_bytes[1]) / 100.0


def parse_linkready(payload: bytes) -> LinkReady | None:
    # FD E2 <slaveID:2> <sign:1> <maxAmps:2> ...
    if len(payload) < 7 or payload[0:2] != b"\xFD\xE2":
        return None
    sender = payload[2:4]
    sign = payload[4]
    max_amps = decode_amps(payload[5:7])
    return LinkReady(sender_id=sender, sign=sign, max_amps=max_amps)


def parse_slave_heartbeat(payload: bytes) -> Heartbeat | None:
    # FD E0 <senderID:2> <receiverID:2> <status+amps:...>
    if len(payload) < 11 or payload[0:2] != b"\xFD\xE0":
        return None
    sender = payload[2:4]
    receiver = payload[4:6]
    data = payload[6:]
    status = data[0]
    amps_max = decode_amps(data[1:3])
    amps_actual = decode_amps(data[3:5])
    return Heartbeat(
        sender_id=sender,
        receiver_id=receiver,
        status=status,
        amps_max=amps_max,
        amps_actual=amps_actual,
        raw=payload,
    )


def build_master_heartbeat(sender_id: bytes, receiver_id: bytes, amps_offer: float, status: int = 0x05) -> bytes:
    body = bytes([status]) + encode_amps(amps_offer) + encode_amps(0.0) + b"\x00\x00\x00\x00"
    return b"\xFB\xE0" + sender_id + receiver_id + body


def build_master_linkready2(sender_id: bytes, sign: int = 0x77) -> bytes:
    return b"\xFB\xE2" + sender_id + bytes([sign]) + b"\x00\x00\x00\x00\x00\x00\x00\x00"
