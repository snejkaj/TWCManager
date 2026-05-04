from __future__ import annotations

from dataclasses import dataclass

FRAME_BOUNDARY = 0xC0
ESCAPE = 0xDB
ESCAPED_C0 = 0xDC
ESCAPED_DB = 0xDD


@dataclass
class ParsedFrame:
    payload: bytes
    checksum_ok: bool


def slip_escape(payload: bytes) -> bytes:
    out = bytearray(payload)
    i = 0
    while i < len(out):
        if out[i] == FRAME_BOUNDARY:
            out[i : i + 1] = bytes([ESCAPE, ESCAPED_C0])
            i += 2
        elif out[i] == ESCAPE:
            out[i : i + 1] = bytes([ESCAPE, ESCAPED_DB])
            i += 2
        else:
            i += 1
    return bytes(out)


def slip_unescape(payload: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(payload):
        b = payload[i]
        if b != ESCAPE:
            out.append(b)
            i += 1
            continue

        if i + 1 >= len(payload):
            out.append(b)
            break

        n = payload[i + 1]
        if n == ESCAPED_C0:
            out.append(FRAME_BOUNDARY)
        elif n == ESCAPED_DB:
            out.append(ESCAPE)
        else:
            out.append(b)
            out.append(n)
        i += 2

    return bytes(out)


def build_twc_frame(msg: bytes) -> bytes:
    checksum = sum(msg[1:]) & 0xFF
    raw = msg + bytes([checksum])
    return bytes([FRAME_BOUNDARY]) + slip_escape(raw) + bytes([FRAME_BOUNDARY])


def parse_twc_frame(frame: bytes) -> ParsedFrame:
    """Parse one raw frame including boundaries."""
    if not frame or frame[0] != FRAME_BOUNDARY or frame[-1] != FRAME_BOUNDARY:
        return ParsedFrame(payload=b"", checksum_ok=False)

    decoded = slip_unescape(frame[1:-1])
    if len(decoded) < 2:
        return ParsedFrame(payload=b"", checksum_ok=False)

    payload = decoded[:-1]
    recv_checksum = decoded[-1]
    calc_checksum = sum(payload[1:]) & 0xFF
    return ParsedFrame(payload=payload, checksum_ok=(recv_checksum == calc_checksum))


def extract_frames(buffer: bytearray) -> list[bytes]:
    """Extract complete frames from a stream buffer and mutate buffer in place."""
    frames: list[bytes] = []

    while True:
        try:
            start = buffer.index(FRAME_BOUNDARY)
        except ValueError:
            buffer.clear()
            break

        if start > 0:
            del buffer[:start]

        try:
            end = buffer.index(FRAME_BOUNDARY, 1)
        except ValueError:
            break

        frame = bytes(buffer[: end + 1])
        del buffer[: end + 1]
        if len(frame) > 2:
            frames.append(frame)

    return frames
