from typing import Dict, List

from BaseClasses import Item, ItemClassification

from .data import ABILITIES, CHAR_INDEX, DEFAULT_CHARACTERS, ROSTER, VANILLA_UNLOCKS

BASE_ID = 0x574F_0000  # "WO"

# Characters that are never shuffled: starting roster, plus the ones the game itself
# unlocks from global conditions that the client leaves alone.
VANILLA_ONLY = {"Zuo Ci", "Orochi", "Da Ji", "Lu Bu", "Honda Tadakatsu"}  # keep in sync: locations.FOURTH_WEAPON_EXCLUDED

STAGE_CHARACTERS: List[str] = [n for n in ROSTER
                               if n in VANILLA_UNLOCKS and VANILLA_UNLOCKS[n].kind == "stage"]
GAIDEN_CHARACTERS: List[str] = [n for n in ROSTER
                                if n in VANILLA_UNLOCKS and VANILLA_UNLOCKS[n].kind == "gaiden"]

FILLER_NAME = "1000 Growth Points"
TRAP_NAMES = ["Musou Drain Trap", "Low Health Trap"]
STORY_NAMES = ["Shu", "Wei", "Wu", "Samurai"]


def stage_unlock_name(story: str) -> str:
    return f"Progressive {story} Stage"


STAGE_UNLOCK_NAMES = [stage_unlock_name(s) for s in STORY_NAMES]


def ability_item_name(ability: str) -> str:
    return f"Ability: {ability}"


ABILITY_ITEM_NAMES = [ability_item_name(a) for a in ABILITIES]

# Item IDs: BASE_ID + roster index for characters, BASE_ID + 0x100 + n for others.
ITEM_NAME_TO_ID: Dict[str, int] = {name: BASE_ID + CHAR_INDEX[name]
                                   for name in STAGE_CHARACTERS + GAIDEN_CHARACTERS}
ITEM_NAME_TO_ID[FILLER_NAME] = BASE_ID + 0x100
for _i, _trap in enumerate(TRAP_NAMES):
    ITEM_NAME_TO_ID[_trap] = BASE_ID + 0x101 + _i
for _i, _name in enumerate(STAGE_UNLOCK_NAMES):
    ITEM_NAME_TO_ID[_name] = BASE_ID + 0x200 + _i
for _i, _name in enumerate(ABILITY_ITEM_NAMES):
    ITEM_NAME_TO_ID[_name] = BASE_ID + 0x300 + _i

ITEM_GROUPS = {"Characters": set(STAGE_CHARACTERS) | set(GAIDEN_CHARACTERS), "Traps": set(TRAP_NAMES),
               "Stage Unlocks": set(STAGE_UNLOCK_NAMES), "Abilities": set(ABILITY_ITEM_NAMES)}
# In Story Mode a character can only be fielded in the story that recruits them
# (confirmed in-game; the recruit table lives at EE 0x0031FBC4).
for _story in ("Shu", "Wei", "Wu", "Samurai"):
    ITEM_GROUPS[f"{_story} Characters"] = {n for n in ITEM_GROUPS["Characters"]
                                            if VANILLA_UNLOCKS[n].story == _story}


class WarriorsOrochiItem(Item):
    game = "Warriors Orochi"


def classification_for(name: str) -> ItemClassification:
    if name == FILLER_NAME:
        return ItemClassification.filler
    if name in TRAP_NAMES:
        return ItemClassification.trap
    if name in ABILITY_ITEM_NAMES:
        return ItemClassification.useful
    return ItemClassification.progression


assert not (set(DEFAULT_CHARACTERS) & set(ITEM_NAME_TO_ID))
assert not (VANILLA_ONLY & set(ITEM_NAME_TO_ID))
