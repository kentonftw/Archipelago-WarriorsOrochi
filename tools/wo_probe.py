"""Warriors Orochi PINE probe.

Usage (PCSX2 running Warriors Orochi with PINE enabled on slot 28011):
    python wo_probe.py            -> one-shot status: game id, roster, Shu progress, growth points
    python wo_probe.py watch      -> logs every byte that changes in the save-data area (Ctrl+C to stop)
                                     and writes the log to wo_watch_log.txt next to this script.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "worlds", "warriors_orochi"))

import data  # noqa: E402
from pine import Pine, PineError, bits_to_set  # noqa: E402

WATCH_START, WATCH_END = 0x004CCF00, 0x004CD600   # everything after the character records


def status(p: Pine) -> None:
    print("PCSX2:", p.version(), "| status:", p.status())
    print("Game ID:", p.game_id())
    bits = p.read_bytes(data.CHAR_UNLOCK_BITS, data.CHAR_UNLOCK_BYTES)
    roster = [data.ROSTER[i] for i in bits_to_set(bits, len(data.ROSTER))]
    print(f"Unlocked characters ({len(roster)}):", ", ".join(roster))
    cleared = []
    for (story, n), rec in data.GAIDEN_RECORDS.items():
        if p.read8(data.STAGE_RECORDS + rec * data.STAGE_RECORD_SIZE + data.STAGE_STATUS_OFFSET) >= data.STAGE_STATUS_CLEARED:
            cleared.append(f"{story} Gaiden {n}")
    print("Gaiden stages cleared:", ", ".join(cleared) or "none")
    for story, addr in data.STORY_PROGRESS.items():
        print(f"{story} progress:", p.read8(addr) if addr is not None else "(address not mapped yet)")
    print("Growth points:", p.read32(data.GROWTH_POINTS))
    print("KO count:", p.read32(data.KO_COUNT))


def watch(p: Pine) -> None:
    log_path = os.path.join(HERE, "wo_watch_log.txt")
    size = WATCH_END - WATCH_START
    prev = p.read_bytes(WATCH_START, size)
    print(f"Watching 0x{WATCH_START:08X}-0x{WATCH_END:08X}. Play normally; changes are logged to {log_path}")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n=== watch started {time.ctime()} ===\n")
        while True:
            p.close()  # PINE serves one program at a time; let the Archipelago client in between reads
            time.sleep(0.5)
            try:
                cur = p.read_bytes(WATCH_START, size)
            except (OSError, PineError):
                continue  # the client was using PINE right then; try again next round
            changes = [(i, prev[i], cur[i]) for i in range(size) if prev[i] != cur[i]]
            # Skip the noisy counters (play time, KO count) so real flags stand out.
            changes = [c for c in changes if not (0x30C <= c[0] < 0x314 or 0x62C <= c[0] < 0x630)]
            if changes:
                stamp = time.strftime("%H:%M:%S")
                text = " ".join(f"{WATCH_START + i:08X}:{a:02X}->{b:02X}" for i, a, b in changes)
                line = f"[{stamp}] {text}"
                print(line)
                log.write(line + "\n")
                log.flush()
            prev = cur


def main() -> None:
    p = Pine()
    try:
        p.connect()
    except OSError as e:
        sys.exit(f"Could not reach PCSX2 PINE on slot 28011 ({e}). Is PINE enabled and the game running?")
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        try:
            watch(p)
        except KeyboardInterrupt:
            print("Stopped.")
    else:
        status(p)


if __name__ == "__main__":
    main()
