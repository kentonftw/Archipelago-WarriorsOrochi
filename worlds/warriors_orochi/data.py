"""Static game data for Warriors Orochi (PS2, NTSC-U, SLUS-21662).

Memory addresses are PS2 EE-RAM addresses (what PCSX2's PINE interface expects).
Everything marked CONFIRMED was verified against live RAM dumps; everything marked
TODO still needs a test in-game before the client can rely on it.
"""
from typing import Dict, List, NamedTuple, Optional, Tuple

GAME_NAME = "Warriors Orochi"
SERIAL = "SLUS-21662"
GAME_CRC = 0x2030F647

# ---------------------------------------------------------------------------
# Memory map
# ---------------------------------------------------------------------------
# CONFIRMED: 79 character records, 0xC8 bytes each, in roster order.
#   +0x00 u32  (unknown, 0xBB8 for Zhao Yun)
#   +0x04 u8   level - 1
#   +0x08 u16  life, musou, attack, defense, speed (5 x u16)
#   +0x14 u16  exp
CHAR_RECORDS = 0x004C9150
CHAR_RECORD_SIZE = 0xC8

# CONFIRMED: 79-bit "character available" bitfield, bit N == roster index N.
# The game commits new bits when you return to camp after the results screens.
CHAR_UNLOCK_BITS = 0x004CCF0C
CHAR_UNLOCK_BYTES = 10

# CONFIRMED: story progress = stages cleared, one u32 per story, 4 bytes apart.
# Shu 1->2 after Shu Stage 2; Wei/Wu/Samurai 0->1 after their Stage 1 (watch log 2026-11-21).
STORY_PROGRESS: Dict[str, Optional[int]] = {
    "Shu": 0x004CCF18,
    "Wei": 0x004CCF1C,
    "Wu": 0x004CCF20,
    "Samurai": 0x004CCF24,
}

# CONFIRMED: 61 per-stage records, 12 bytes each: u32 best time (frames, 0x34BC0 = none),
# u32 best KOs, u32 status (0 locked, 1/2 available, 3 cleared).
# Record N lines up with recruit-table entry N at EE 0x0031FBCA (6 bytes each).
STAGE_RECORDS = 0x004CCF28
STAGE_RECORD_SIZE = 12
STAGE_STATUS_OFFSET = 8
STAGE_STATUS_CLEARED = 3
STAGE_STATUS_LOCKED = 0     # CONFIRMED: writing 0 hides a stage from Select Scenario
STAGE_STATUS_OPEN = 2       # CONFIRMED: writing 2 makes a stage selectable

# Record index of every stage. Identified from the recruit table at RECRUIT_TABLE: bytes 1-3 are the
# stage's recruits and byte 4/5 are its "personal item" characters, matched against the community
# unlock and personal-item lists (koei fandom, GameFAQs). CONFIRMED in-game: Shu 2, Shu G2, Wei 1,
# Wu 1, Samurai 1, Samurai 2 (watch logs). Record 60 is not a stage.
GAIDEN_RECORDS: Dict[Tuple[str, int], int] = {
    ("Shu", 2): 4, ("Shu", 3): 45, ("Shu", 4): 16, ("Shu", 5): 26, ("Shu", 6): 55, ("Shu", 7): 0, ("Shu", 8): 53,
    ("Wei", 2): 20, ("Wei", 3): 5, ("Wei", 4): 51, ("Wei", 5): 32, ("Wei", 6): 2, ("Wei", 7): 1, ("Wei", 8): 28,
    ("Wu", 2): 8, ("Wu", 3): 33, ("Wu", 4): 31, ("Wu", 5): 34, ("Wu", 6): 50, ("Wu", 7): 3, ("Wu", 8): 15,
    ("Samurai", 2): 42, ("Samurai", 3): 11, ("Samurai", 4): 6, ("Samurai", 5): 48, ("Samurai", 6): 39,
    ("Samurai", 7): 41, ("Samurai", 8): 29,
}
# Gaiden 8 ("Last Gaiden") only opens after a special objective in Chapter 7.
LAST_GAIDEN = 8
STORY_RECORDS: Dict[Tuple[str, int], int] = {
    ("Shu", 1): 35, ("Shu", 2): 49, ("Shu", 3): 18, ("Shu", 4): 24, ("Shu", 5): 10, ("Shu", 6): 7,
    ("Shu", 7): 36, ("Shu", 8): 58,
    ("Wei", 1): 47, ("Wei", 2): 25, ("Wei", 3): 13, ("Wei", 4): 23, ("Wei", 5): 40, ("Wei", 6): 27,
    ("Wei", 7): 54, ("Wei", 8): 56,
    ("Wu", 1): 21, ("Wu", 2): 14, ("Wu", 3): 38, ("Wu", 4): 37, ("Wu", 5): 46, ("Wu", 6): 19,
    ("Wu", 7): 44, ("Wu", 8): 57,
    ("Samurai", 1): 9, ("Samurai", 2): 52, ("Samurai", 3): 43, ("Samurai", 4): 17, ("Samurai", 5): 12,
    ("Samurai", 6): 22, ("Samurai", 7): 30, ("Samurai", 8): 59,
}
RECRUIT_TABLE = 0x0031FBCA  # 61 x 6 bytes; 1-3 = recruits, 4-5 = personal-item characters (0x4F = none)

GROWTH_POINTS = 0x004CD210       # CONFIRMED u32 (6020 -> 12637 -> spent 470 = 11505)
KO_COUNT = 0x004CD52C            # CONFIRMED u32, resets to 0 at camp
PLAYER_HP = 0x004DD5C0           # from decrypted CodeBreaker codes (u16 max, u16 current)
PLAYER_MUSOU_MAX = 0x004DD5C6    # u16, from decrypted "Max Musou P1"
PLAYER_MUSOU = 0x004DD5C8        # u16 current, from decrypted "Infinite Musou P1"
PLAYER_UNIT_MARKER = 0x004DD5B4  # 0xFFFFFFFF while a player unit is live (PROBABLE)
KO_MILESTONES = [100, 200, 300, 500, 750, 1000]

# Abilities are shared by the whole army (CONFIRMED 2026-11-22 via the Abilities screen).
# 18 bytes, one per ability: value = level - 1, 20 = not acquired. Order = the screen grid, column by column.
ABILITY_LEVELS = 0x004CD21B
ABILITY_NONE = 20
ABILITIES_IN_USE = 0x004CD214   # 7 bytes of ability ids, 18 = empty slot
ABILITY_SLOT_EMPTY = 18
ABILITIES = ["Vitality", "Focus", "Potence", "Fortitude", "Impulse", "Cavalier",
             "Karma", "Power", "Speed", "Technique", "Boost", "Awakening",
             "Acclaim", "Recuperate", "Conserve", "Adrenalin", "Recover", "Refill"]

# In-game notices (CONFIRMED 2026-11-22). The game looks its pop-up texts up through a pointer table at
# 0x331F18; the strings below live in the main executable's data, so they stay put. Text supports
# printf %s and colour codes like "[01word]" (01 = red). Each slot holds 47 characters + terminator.
MSG_NEW_OFFICER = 0x0032E780     # "%s has become available for use."  (stage-clear recruit notice)
MSG_NEW_SCENARIO = 0x0032E7B0    # "A new scenario has become available."
MSG_SLOT_LEN = 47
MSG_NEW_OFFICER_ORIGINAL = "%s has become available for use."
MSG_NEW_SCENARIO_ORIGINAL = "A new scenario has become available."
CURRENT_STAGE_RECORD = 0x004CD4F4  # u8 stage record index of the battle being played (CONFIRMED: 35 = Shu 1, 47 = Wei 1)

# Weapon inventory inside each character record (CONFIRMED 2026-11-22 via a weapon pickup;
# saved to the record when returning to camp). Slot = u16 weapon id + 20 bytes of attributes.
WEAPON_SLOTS_OFFSET = 0x18
WEAPON_SLOT_SIZE = 0x16
WEAPON_SLOTS = 7
WEAPON_EMPTY = 0x159


def weapon_id(char_index: int, level: int) -> int:
    """Weapon ids are char_index * 4 + level - 1 (Hideyoshi #63 level 1 = 252)."""
    return char_index * 4 + level - 1
MOVIE_UNLOCK_BITS = 0x004CD22F   # from decrypted "Unlock All Movies" code
CURRENT_STAGE_ID = 0x004CD236    # PROBABLE: 0x0C while playing/after Shu Stage 2

# 16-byte signature of game code at EE 0x00120000, used by the Cheat Engine dump helper
# to locate EE RAM inside the PCSX2 process. Not needed with PINE.
CODE_SIGNATURE_AT_0x120000 = bytes.fromhex("0d0040142d200002f681040c000000002d2000022d884000")

# ---------------------------------------------------------------------------
# Roster (index == bit in CHAR_UNLOCK_BITS == record index). CONFIRMED order:
# read from the game's own name table at EE 0x00321048.
# ---------------------------------------------------------------------------
ROSTER: List[str] = [
    "Zhao Yun", "Guan Yu", "Zhang Fei", "Xiahou Dun", "Dian Wei", "Xu Zhu", "Zhou Yu", "Lu Xun",
    "Taishi Ci", "Diao Chan", "Zhuge Liang", "Cao Cao", "Lu Bu", "Sun Shang Xiang", "Liu Bei",
    "Sun Jian", "Sun Quan", "Dong Zhuo", "Yuan Shao", "Ma Chao", "Huang Zhong", "Xiahou Yuan",
    "Zhang Liao", "Sima Yi", "Lu Meng", "Gan Ning", "Jiang Wei", "Zhang Jiao", "Xu Huang",
    "Zhang He", "Zhen Ji", "Huang Gai", "Sun Ce", "Wei Yan", "Pang Tong", "Meng Huo", "Zhu Rong",
    "Da Qiao", "Xiao Qiao", "Cao Ren", "Zhou Tai", "Yue Ying", "Cao Pi", "Pang De", "Ling Tong",
    "Guan Ping", "Xing Cai", "Zuo Ci",
    "Sanada Yukimura", "Maeda Keiji", "Oda Nobunaga", "Akechi Mitsuhide", "Ishikawa Goemon",
    "Uesugi Kenshin", "Oichi", "Okuni", "Kunoichi", "Saika Magoichi", "Takeda Shingen",
    "Date Masamune", "Lady Noh", "Hattori Hanzo", "Mori Ranmaru", "Toyotomi Hideyoshi",
    "Imagawa Yoshimoto", "Honda Tadakatsu", "Inahime", "Tokugawa Ieyasu", "Ishida Mitsunari",
    "Azai Nagamasa", "Shima Sakon", "Shimazu Yoshihiro", "Tachibana Ginchiyo", "Naoe Kanetsugu",
    "Nene", "Fuma Kotaro", "Miyamoto Musashi", "Orochi", "Da Ji",
]
assert len(ROSTER) == 79
CHAR_INDEX = {name: i for i, name in enumerate(ROSTER)}

STORIES = ["Shu", "Wei", "Wu", "Samurai"]
STAGES_PER_STORY = 8

# CONFIRMED by the bits set on a fresh save: 3 starting characters per story.
DEFAULT_CHARACTERS = [
    "Zhao Yun", "Xing Cai", "Shimazu Yoshihiro",           # Shu
    "Cao Pi", "Zhang Liao", "Xu Huang",                    # Wei
    "Sun Ce", "Hattori Hanzo", "Tokugawa Ieyasu",          # Wu
    "Oda Nobunaga", "Akechi Mitsuhide", "Toyotomi Hideyoshi",  # Samurai
]


class Unlock(NamedTuple):
    kind: str            # "stage", "gaiden" or "special"
    story: Optional[str]
    stage: int           # story stage / gaiden number it belongs to (0 for special)
    note: str


def _s(story: str, n: int) -> Unlock:
    return Unlock("stage", story, n, f"Clear {story} Stage {n}")


def _g(story: str, n: int, note: str) -> Unlock:
    return Unlock("gaiden", story, n, f"{story} Gaiden {n}: {note}")


# Vanilla unlock conditions (community cheat sites; cross-checked where possible).
VANILLA_UNLOCKS: Dict[str, Unlock] = {
    # Shu story
    "Tachibana Ginchiyo": _s("Shu", 1),        # CONFIRMED in RAM
    "Yue Ying": _s("Shu", 2),                  # CONFIRMED in RAM
    "Saika Magoichi": _s("Shu", 2),            # CONFIRMED in RAM
    "Sanada Yukimura": _s("Shu", 3), "Wei Yan": _s("Shu", 3),
    "Meng Huo": _s("Shu", 4), "Zhu Rong": _s("Shu", 4),
    "Yuan Shao": _s("Shu", 5),
    "Guan Yu": _s("Shu", 7), "Zhang Fei": _s("Shu", 7), "Zhuge Liang": _s("Shu", 7),
    "Liu Bei": _s("Shu", 8),
    "Jiang Wei": _g("Shu", 2, "initiate Jiang Wei's ambush plan"),
    "Pang De": _g("Shu", 3, "rescue all of the Hojo (yellow) generals"),
    "Ishikawa Goemon": _g("Shu", 4, "break all of Goemon's treasure boxes"),
    "Date Masamune": _g("Shu", 5, "complete the optional missions"),
    "Miyamoto Musashi": _g("Shu", 6, "open the dam and keep all yellow swordsmen alive"),
    # Wei story
    "Xu Zhu": _s("Wei", 1),  # CONFIRMED in RAM
    "Ishida Mitsunari": _s("Wei", 2),
    "Pang Tong": _s("Wei", 4), "Xiahou Dun": _s("Wei", 4), "Xiahou Yuan": _s("Wei", 4),
    "Huang Gai": _s("Wei", 5),
    "Azai Nagamasa": _s("Wei", 6), "Gan Ning": _s("Wei", 6), "Oichi": _s("Wei", 6),
    "Cao Cao": _s("Wei", 7), "Dian Wei": _s("Wei", 7),
    "Zhang He": _g("Wei", 2, "rescue Zhang He and defend the HQ"),
    "Nene": _g("Wei", 3, "defeat both Nene clones within 4 minutes"),
    "Imagawa Yoshimoto": _g("Wei", 4, "keep all ploy troops out of the village"),
    "Diao Chan": _g("Wei", 5, "Diao Chan must survive"),
    "Zhen Ji": _g("Wei", 6, "defeat all magicians and the fake Cao Pi"),
    # Wu story
    "Mori Ranmaru": _s("Wu", 1), "Zhou Yu": _s("Wu", 1), "Taishi Ci": _s("Wu", 2),
    "Lu Meng": _s("Wu", 3), "Shima Sakon": _s("Wu", 3), "Xiao Qiao": _s("Wu", 3),
    "Inahime": _s("Wu", 5), "Sun Shang Xiang": _s("Wu", 5),
    "Zhou Tai": _s("Wu", 6), "Sun Jian": _s("Wu", 7), "Sun Quan": _s("Wu", 7),
    "Fuma Kotaro": _g("Wu", 2, "defeat Kotaro after all supply troops reach your HQ"),
    "Lady Noh": _g("Wu", 3, "defeat all messengers without using Nobunaga"),
    "Kunoichi": _g("Wu", 4, "escort all peasants"),
    "Da Qiao": _g("Wu", 5, "meet Da Qiao before the enemy does"),
    "Maeda Keiji": _g("Wu", 6, "lead the drum reinforcements to the main camp in time"),
    # Samurai (Sengoku) story
    "Guan Ping": _s("Samurai", 1), "Huang Zhong": _s("Samurai", 1),
    "Okuni": _s("Samurai", 3), "Zhang Jiao": _s("Samurai", 3), "Ling Tong": _s("Samurai", 5),
    "Naoe Kanetsugu": _s("Samurai", 7), "Takeda Shingen": _s("Samurai", 7),
    "Uesugi Kenshin": _s("Samurai", 7),
    "Ma Chao": _g("Samurai", 2, "all peasants escape and Ma Chao survives"),
    "Lu Xun": _g("Samurai", 3, "escort Lu Xun to your HQ"),
    "Dong Zhuo": _g("Samurai", 4, "stop all supply captains reaching Dong Zhuo"),
    "Cao Ren": _g("Samurai", 5, "rescue the Takeda-Uesugi army, then defeat Cao Ren"),
    "Sima Yi": _g("Samurai", 6, "kill the two retreating Orochi generals"),
    # Special
    "Honda Tadakatsu": Unlock("special", None, 7, "Impress Honda in Gaiden 7 of all four stories"),
    "Lu Bu": Unlock("special", None, 8, "Defeat Lu Bu in Gaiden 8 of all four stories"),
    "Zuo Ci": Unlock("special", None, 8, "Clear all four stories"),
    "Da Ji": Unlock("special", None, 8, "Clear every stage, including all Gaiden stages"),
    "Orochi": Unlock("special", None, 8, "Unlock every other character"),
}

assert set(VANILLA_UNLOCKS) | set(DEFAULT_CHARACTERS) == set(ROSTER), \
    set(ROSTER) - set(VANILLA_UNLOCKS) - set(DEFAULT_CHARACTERS)
