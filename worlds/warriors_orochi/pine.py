"""Minimal client for PCSX2's PINE interface (memory read/write over a local socket).

Protocol (PCSX2 / PINE spec):
  request : u32 total_size (including these 4 bytes) | one or more commands
  command : u8 opcode | u32 address | [value]
  reply   : u32 total_size | u8 result (0 = OK, 0xFF = FAIL) | [data per command]
On Windows PINE listens on TCP 127.0.0.1:<slot> (default slot 28011).
On Linux/macOS it is a unix socket: $XDG_RUNTIME_DIR/pcsx2.sock (or /tmp/pcsx2.sock),
with ".<slot>" appended when the slot is not the default.
"""
import os
import socket
import struct
import sys
from typing import List, Optional

DEFAULT_SLOT = 28011

OP_READ8, OP_READ16, OP_READ32, OP_READ64 = 0x00, 0x01, 0x02, 0x03
OP_WRITE8, OP_WRITE16, OP_WRITE32, OP_WRITE64 = 0x04, 0x05, 0x06, 0x07
OP_VERSION, OP_TITLE, OP_ID, OP_STATUS = 0x08, 0x0B, 0x0C, 0x0F

RESULT_OK = 0x00

STATUS_NAMES = {0: "running", 1: "paused", 2: "shutdown"}


class PineError(Exception):
    pass


class Pine:
    def __init__(self, slot: int = DEFAULT_SLOT, timeout: float = 2.0):
        self.slot = slot
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    # -- connection -------------------------------------------------------------
    def connect(self) -> None:
        self.close()
        if sys.platform == "win32":
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect(("127.0.0.1", self.slot))
        else:
            env = "TMPDIR" if sys.platform == "darwin" else "XDG_RUNTIME_DIR"
            base = os.environ.get(env) or "/tmp"
            path = os.path.join(base, "pcsx2.sock")
            if self.slot != DEFAULT_SLOT:
                path += f".{self.slot}"
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect(path)
        self.sock = s

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    @property
    def connected(self) -> bool:
        return self.sock is not None

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise PineError("PCSX2 closed the PINE connection")
            buf += chunk
        return buf

    def _call(self, commands: bytes) -> bytes:
        if self.sock is None:
            self.connect()
        packet = struct.pack("<I", len(commands) + 4) + commands
        try:
            self.sock.sendall(packet)
            size = struct.unpack("<I", self._recv_exact(4))[0]
            body = self._recv_exact(size - 4)
        except (OSError, PineError):
            self.close()
            raise
        if body[0] != RESULT_OK:
            raise PineError("PINE command failed (is a game running?)")
        return body[1:]

    # -- memory ---------------------------------------------------------------
    def read8(self, addr: int) -> int:
        return self._call(struct.pack("<BI", OP_READ8, addr))[0]

    def read16(self, addr: int) -> int:
        return struct.unpack("<H", self._call(struct.pack("<BI", OP_READ16, addr)))[0]

    def read32(self, addr: int) -> int:
        return struct.unpack("<I", self._call(struct.pack("<BI", OP_READ32, addr)))[0]

    def read_bytes(self, addr: int, length: int) -> bytes:
        """Reads length bytes in one batched request (byte-wise, keeps alignment simple)."""
        cmds = b"".join(struct.pack("<BI", OP_READ8, addr + i) for i in range(length))
        return self._call(cmds)

    def read8_many(self, addrs) -> List[int]:
        """Reads several bytes in one batched request."""
        addrs = list(addrs)
        if not addrs:
            return []
        return list(self._call(b"".join(struct.pack("<BI", OP_READ8, a) for a in addrs)))

    def read16_many(self, addrs) -> List[int]:
        """Reads several u16 values in one batched request."""
        addrs = list(addrs)
        if not addrs:
            return []
        data = self._call(b"".join(struct.pack("<BI", OP_READ16, a) for a in addrs))
        return list(struct.unpack(f"<{len(addrs)}H", data))

    def write8(self, addr: int, value: int) -> None:
        self._call(struct.pack("<BIB", OP_WRITE8, addr, value & 0xFF))

    def write16(self, addr: int, value: int) -> None:
        self._call(struct.pack("<BIH", OP_WRITE16, addr, value & 0xFFFF))

    def write32(self, addr: int, value: int) -> None:
        self._call(struct.pack("<BII", OP_WRITE32, addr, value & 0xFFFFFFFF))

    def write_bytes(self, addr: int, data: bytes) -> None:
        cmds = b"".join(struct.pack("<BIB", OP_WRITE8, addr + i, b) for i, b in enumerate(data))
        self._call(cmds)

    # -- emulator info --------------------------------------------------------
    def _string(self, op: int) -> str:
        data = self._call(struct.pack("<B", op))
        size = struct.unpack_from("<I", data)[0]
        return data[4:4 + size].split(b"\0")[0].decode("utf-8", "replace")

    def version(self) -> str:
        return self._string(OP_VERSION)

    def game_id(self) -> str:
        return self._string(OP_ID)

    def title(self) -> str:
        return self._string(OP_TITLE)

    def status(self) -> str:
        code = struct.unpack("<I", self._call(struct.pack("<B", OP_STATUS)))[0]
        return STATUS_NAMES.get(code, f"unknown({code})")


def bits_to_set(data: bytes, count: int) -> List[int]:
    return [i for i in range(count) if data[i // 8] >> (i % 8) & 1]


def set_to_bits(indices, nbytes: int) -> bytes:
    out = bytearray(nbytes)
    for i in indices:
        out[i // 8] |= 1 << (i % 8)
    return bytes(out)
