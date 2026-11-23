from typing import Dict

from BaseClasses import Location

from .data import ABILITIES, CHAR_INDEX, GAIDEN_RECORDS, KO_MILESTONES, STAGES_PER_STORY, STORIES, VANILLA_UNLOCKS
from .items import GAIDEN_CHARACTERS

BASE_ID = 0x574F_1000


def stage_location(story: str, n: int) -> str:
    return f"{story} Stage {n} Cleared"


def gaiden_stage_location(story: str, n: int) -> str:
    return f"{story} Gaiden {n} Cleared"


def gaiden_location(character: str) -> str:
    return f"{VANILLA_UNLOCKS[character].note} ({character})"


STAGE_LOCATIONS = {stage_location(s, n): (s, n) for s in STORIES for n in range(1, STAGES_PER_STORY + 1)}
GAIDEN_LOCATIONS = {gaiden_location(c): c for c in GAIDEN_CHARACTERS}
GAIDEN_STAGE_LOCATIONS = {gaiden_stage_location(s, n): (s, n) for (s, n) in GAIDEN_RECORDS}

LOCATION_NAME_TO_ID: Dict[str, int] = {}
for i, story in enumerate(STORIES):
    for n in range(1, STAGES_PER_STORY + 1):
        LOCATION_NAME_TO_ID[stage_location(story, n)] = BASE_ID + i * 0x10 + n
for c in GAIDEN_CHARACTERS:
    # 0x100 + roster index, so the client can map a set bit straight to a location.
    LOCATION_NAME_TO_ID[gaiden_location(c)] = BASE_ID + 0x100 + CHAR_INDEX[c]

for i, story in enumerate(STORIES):
    for n in range(2, STAGES_PER_STORY + 1):
        if (story, n) in GAIDEN_RECORDS:
            LOCATION_NAME_TO_ID[gaiden_stage_location(story, n)] = BASE_ID + 0x80 + i * 0x10 + n

def ko_location(count: int) -> str:
    return f"{count} KOs in One Battle"


KO_LOCATIONS = {ko_location(c): c for c in KO_MILESTONES}
for _i, _c in enumerate(KO_MILESTONES):
    LOCATION_NAME_TO_ID[ko_location(_c)] = BASE_ID + 0x200 + _i

# 4th weapons: every character except the ones the game unlocks only from global conditions.
FOURTH_WEAPON_EXCLUDED = {"Zuo Ci", "Orochi", "Da Ji", "Lu Bu", "Honda Tadakatsu"}


def weapon_location(character: str) -> str:
    return f"{character}'s 4th Weapon"


WEAPON_LOCATIONS = {weapon_location(c): c for c in CHAR_INDEX if c not in FOURTH_WEAPON_EXCLUDED}
for _c in CHAR_INDEX:
    if _c not in FOURTH_WEAPON_EXCLUDED:
        LOCATION_NAME_TO_ID[weapon_location(_c)] = BASE_ID + 0x300 + CHAR_INDEX[_c]

def ability_location(ability: str) -> str:
    return f"Earn Ability: {ability}"


ABILITY_LOCATIONS = {ability_location(a): a for a in ABILITIES}
for _i, _a in enumerate(ABILITIES):
    LOCATION_NAME_TO_ID[ability_location(_a)] = BASE_ID + 0x400 + _i

LOCATION_GROUPS = {story: {stage_location(story, n) for n in range(1, STAGES_PER_STORY + 1)}
                   for story in STORIES}
LOCATION_GROUPS["Gaiden Unlocks"] = set(GAIDEN_LOCATIONS)
LOCATION_GROUPS["Gaiden Stages"] = set(GAIDEN_STAGE_LOCATIONS)
LOCATION_GROUPS["KO Milestones"] = set(KO_LOCATIONS)
LOCATION_GROUPS["4th Weapons"] = set(WEAPON_LOCATIONS)
LOCATION_GROUPS["Abilities"] = set(ABILITY_LOCATIONS)


class WarriorsOrochiLocation(Location):
    game = "Warriors Orochi"
