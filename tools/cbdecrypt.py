"""CodeBreaker PS2 (V1 + V7) code decryptor.

Python port of the algorithm in cb2util's cb2_crypto.c (MIT, Mathias Lafeldt).
Usage: python3 cbdecrypt.py codes.txt   (lines of "XXXXXXXX YYYYYYYY", names allowed)
"""
import struct
import sys

from cbtables import DEFKEY, DEFSEEDS, SEEDTABLE

M = 0xFFFFFFFF
ST = [SEEDTABLE[0:16], SEEDTABLE[16:32], SEEDTABLE[32:48]]
RSA_N = 0xFFFFFFFFFFFFFFF5
RSA_D = 11


def rc4(key: bytes, data: bytearray):
    """Returns a stateful crypt function initialised with key."""
    perm = list(range(256))
    j = 0
    for i in range(256):
        j = (j + perm[i] + key[i % len(key)]) & 0xFF
        perm[i], perm[j] = perm[j], perm[i]
    st = {"i": 0, "j": 0}

    def crypt(buf: bytearray):
        for k in range(len(buf)):
            st["i"] = (st["i"] + 1) & 0xFF
            st["j"] = (st["j"] + perm[st["i"]]) & 0xFF
            a, b = st["i"], st["j"]
            perm[a], perm[b] = perm[b], perm[a]
            buf[k] ^= perm[(perm[a] + perm[b]) & 0xFF]

    return crypt


def mod_inverse(x):
    y = x
    for _ in range(4):
        y = (y * (2 - y * x)) & M
    return y


class CB:
    def __init__(self):
        self.mode = "raw"
        self.v7_init = False
        self.beefcodf = 0
        self.code_lines = 0
        self.seeds = [bytearray(256) for _ in range(5)]
        self.key = [0] * 5

    def _keybytes(self):
        return b"".join(struct.pack("<I", k & M) for k in self.key)

    def _setkey_from(self, val):
        p = struct.pack("<I", val)
        s = self.seeds
        self.key[0] = (s[3][p[3]] << 24) | (s[2][p[2]] << 16) | (s[1][p[1]] << 8) | s[0][p[0]]
        self.key[1] = (s[0][p[3]] << 24) | (s[3][p[2]] << 16) | (s[2][p[1]] << 8) | s[1][p[0]]
        self.key[2] = (s[1][p[3]] << 24) | (s[0][p[2]] << 16) | (s[3][p[1]] << 8) | s[2][p[0]]
        self.key[3] = (s[2][p[3]] << 24) | (s[1][p[2]] << 16) | (s[0][p[1]] << 8) | s[3][p[0]]

    def beefcode(self, init, val):
        if init:
            self.beefcodf = 0
            self.key = list(DEFKEY)
            if val:
                self.seeds = [bytearray(DEFSEEDS[i * 256:(i + 1) * 256]) for i in range(5)]
                self._setkey_from(val)
            else:
                self.seeds = [bytearray(256) for _ in range(5)]
        else:
            if val:
                self._setkey_from(val)
            else:
                self.seeds = [bytearray(256) for _ in range(5)]
                self.key[0:4] = [0, 0, 0, 0]
        for i in range(5):
            crypt = rc4(self._keybytes(), None)
            crypt(self.seeds[i])
            kb = bytearray(self._keybytes())
            crypt(kb)
            self.key = list(struct.unpack("<5I", bytes(kb)))

    def _s32(self, n, i):
        return struct.unpack_from("<I", self.seeds[n], i * 4)[0]

    def v1_decrypt(self, addr, val):
        cmd = addr >> 28
        if cmd > 2:
            val = ((addr ^ val) - ST[2][cmd]) & M
        tmp = addr ^ ST[0][cmd]
        addr = (tmp - ST[1][cmd]) & M
        addr = (tmp & 0xFF000000) | ((addr & 0xFFFF) << 8) | ((addr >> 16) & 0xFF)
        return addr, val

    def v7_decrypt(self, addr, val):
        for i in range(63, -1, -1):
            val = (((val - (addr ^ self._s32(4, i))) ^ self._s32(1, i)) + self._s32(3, i)) & M
            addr = (((addr + (val ^ self._s32(4, i))) ^ self._s32(0, i)) - self._s32(2, i)) & M
        code = (addr << 32) | val
        if code < RSA_N:
            code = pow(code, RSA_D, RSA_N)
            addr, val = code >> 32, code & M
        buf = bytearray(struct.pack("<II", addr, val))
        rc4(self._keybytes(), None)(buf)
        addr, val = struct.unpack("<II", bytes(buf))
        addr = (addr * mod_inverse(((self.key[0] - self.key[1]) & M) | 1)) & M
        val = (val * mod_inverse(((self.key[2] + self.key[3]) & M) | 1)) & M
        if self.beefcodf:
            buf = bytearray(b"".join(bytes(s) for s in self.seeds))
            rc4(struct.pack("<II", addr, val), None)(buf)
            self.seeds = [bytearray(buf[i * 256:(i + 1) * 256]) for i in range(5)]
            self.beefcodf = 0
            return addr, val
        if (addr & 0xFFFFFFFE) == 0xBEEFC0DE:
            self.beefcode(False, val)
        return addr, val

    @staticmethod
    def num_lines(addr):
        cmd = addr >> 28
        if cmd < 3 or cmd > 6:
            return 1
        if cmd == 3:
            return 2 if addr & 0x00400000 else 1
        return 2

    def decrypt2(self, addr, val):
        """Port of cb_decrypt_code2 (auto-detects raw / V1 / V7)."""
        if self.mode != "v7":
            if not self.code_lines:
                if (addr >> 24) & 0x0E:
                    if (addr & 0xFFFFFFFE) == 0xBEEFC0DE:
                        return addr, val
                    self.mode = "v1"
                    addr, val = self.v1_decrypt(addr, val)
                else:
                    self.mode = "raw"
                self.code_lines = self.num_lines(addr) - 1
            else:
                self.code_lines -= 1
                if self.mode == "raw":
                    return addr, val
                addr, val = self.v1_decrypt(addr, val)
        else:
            addr, val = self.v7_decrypt(addr, val)
            if not self.code_lines:
                self.code_lines = self.num_lines(addr)
                if self.code_lines == 1 and addr == 0xFFFFFFFF:
                    self.code_lines = 0
                    return addr, val
            self.code_lines -= 1
        if (addr & 0xFFFFFFFE) == 0xBEEFC0DE:
            self.beefcode(not self.v7_init, val)
            self.v7_init = True
            self.mode = "v7"
            self.beefcodf = addr & 1
            self.code_lines = 1
        return addr, val


if __name__ == "__main__":
    import re

    cb = CB()
    for line in open(sys.argv[1]):
        m = re.match(r"\s*([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*$", line)
        if not m:
            print(line.rstrip())
            continue
        a, v = cb.decrypt2(int(m.group(1), 16), int(m.group(2), 16))
        print(f"{a:08X} {v:08X}")
