"""Warriors Orochi (PS2) world for Archipelago.

Items are characters: you only get to pick a character once someone sends it to you.
Checks are story stage clears (and, optionally, the Gaiden objectives that normally unlock a character).
"""
from typing import Any, Dict, List

from BaseClasses import ItemClassification, LocationProgressType, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch

from .data import DEFAULT_CHARACTERS, GAME_NAME, LAST_GAIDEN, STAGES_PER_STORY, STORIES, VANILLA_UNLOCKS
from .items import (ABILITY_ITEM_NAMES, FILLER_NAME, STAGE_UNLOCK_NAMES, stage_unlock_name, GAIDEN_CHARACTERS, ITEM_GROUPS, ITEM_NAME_TO_ID, STAGE_CHARACTERS, TRAP_NAMES,
                    WarriorsOrochiItem, classification_for)
from .locations import (GAIDEN_LOCATIONS, GAIDEN_STAGE_LOCATIONS, ABILITY_LOCATIONS, KO_LOCATIONS, LOCATION_GROUPS, WEAPON_LOCATIONS, LOCATION_NAME_TO_ID,
                        STAGE_LOCATIONS, WarriorsOrochiLocation)

HARD_KO_COUNT = 500    # KO milestones from here up expect a Stage 5 in some story
HARD_KO_STAGE = 5
from .options import WarriorsOrochiOptions


def launch_client(*args: str) -> None:
    from .client import launch as client_main
    launch(client_main, name="Warriors Orochi Client", args=args)


components.append(Component("Warriors Orochi Client", func=launch_client, game_name=GAME_NAME,
                            component_type=Type.CLIENT, supports_uri=True))


class WarriorsOrochiWeb(WebWorld):
    theme = "stone"
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "How to play Warriors Orochi (PS2) with Archipelago using PCSX2.",
        "English", "setup_en.md", "setup/en", ["Warriors Orochi AP contributors"])]


class WarriorsOrochiWorld(World):
    """
    Orochi has torn the Three Kingdoms and the Warring States apart. In this randomizer the
    officers who would normally join you after each battle are scattered across the multiworld.
    """
    game = GAME_NAME
    web = WarriorsOrochiWeb()
    options_dataclass = WarriorsOrochiOptions
    options: WarriorsOrochiOptions

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID
    item_name_groups = ITEM_GROUPS
    location_name_groups = LOCATION_GROUPS
    origin_region_name = "Menu"

    def shuffled_characters(self) -> List[str]:
        chars = list(STAGE_CHARACTERS)
        if self.options.gaiden_unlock_checks:
            chars += GAIDEN_CHARACTERS
        return chars

    def story_pool(self, story: str) -> int:
        return len([n for n in self.shuffled_characters() if VANILLA_UNLOCKS[n].story == story])

    def stage_rule(self, story: str, n: int):
        req = min(self.options.story_character_requirement.value, self.story_pool(story))
        need = req * (n - 1) // (STAGES_PER_STORY - 1)
        keys = n - 1 if self.options.stage_locks else 0
        player, group, key = self.player, f"{story} Characters", stage_unlock_name(story)
        if need <= 0 and keys <= 0:
            return None
        if keys <= 0:
            return lambda state: state.has_group(group, player, need)
        if need <= 0:
            return lambda state: state.has(key, player, keys)
        return lambda state: state.has(key, player, keys) and state.has_group(group, player, need)

    # -- generation steps -----------------------------------------------------
    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        names = list(STAGE_LOCATIONS)
        if self.options.gaiden_stage_checks:
            names += [n for n, (_, stage) in GAIDEN_STAGE_LOCATIONS.items()
                      if stage < LAST_GAIDEN or self.options.last_gaiden_checks]
        if self.options.gaiden_unlock_checks:
            names += list(GAIDEN_LOCATIONS)
        names += [n for n, count in KO_LOCATIONS.items() if count <= self.options.ko_milestone_max.value]
        if self.options.fourth_weapon_checks:
            names += list(WEAPON_LOCATIONS)
        if self.options.ability_shuffle:
            names += list(ABILITY_LOCATIONS)
        for name in names:
            loc = WarriorsOrochiLocation(self.player, name, LOCATION_NAME_TO_ID[name], menu)
            if name in ABILITY_LOCATIONS:
                loc.progress_type = LocationProgressType.EXCLUDED  # unlock conditions not mapped
            if name in KO_LOCATIONS or name in WEAPON_LOCATIONS or name in ABILITY_LOCATIONS:
                menu.locations.append(loc)
                continue
            if name in STAGE_LOCATIONS:
                story, n = STAGE_LOCATIONS[name]
            elif name in GAIDEN_STAGE_LOCATIONS:
                story, n = GAIDEN_STAGE_LOCATIONS[name]
            else:
                unlock = VANILLA_UNLOCKS[GAIDEN_LOCATIONS[name]]
                story, n = unlock.story, unlock.stage
            rule = self.stage_rule(story, n)
            if rule:
                loc.access_rule = rule
            menu.locations.append(loc)

        # KO milestones: any character can farm KOs, but the big ones want a later stage.
        hard = [self.stage_rule(s, HARD_KO_STAGE) for s in STORIES]
        if all(hard):
            for loc in menu.locations:
                if loc.name in KO_LOCATIONS and KO_LOCATIONS[loc.name] >= HARD_KO_COUNT:
                    loc.access_rule = lambda state, rules=hard: any(r(state) for r in rules)

        # 4th weapons: need the character, plus Hard 3-star stages (a Stage 5 somewhere).
        shuffled = set(self.shuffled_characters())
        for loc in menu.locations:
            if loc.name not in WEAPON_LOCATIONS:
                continue
            char = WEAPON_LOCATIONS[loc.name]
            if char in shuffled:
                has_char = lambda state, c=char: state.has(c, self.player)
            elif char in DEFAULT_CHARACTERS:
                has_char = None
            else:  # unlocked by the game itself: reaching its vanilla unlock stage
                unlock = VANILLA_UNLOCKS[char]
                has_char = self.stage_rule(unlock.story, unlock.stage)
            parts = [r for r in [has_char] + ([lambda state, rules=hard: any(r(state) for r in rules)]
                                                if all(hard) else []) if r]
            if parts:
                loc.access_rule = lambda state, parts=parts: all(p(state) for p in parts)

        goal = WarriorsOrochiLocation(self.player, "Stories Cleared", None, menu)
        need = self.options.stories_required.value
        finals = [self.stage_rule(s, STAGES_PER_STORY) for s in STORIES]
        if any(finals):
            finals = [r or (lambda state: True) for r in finals]
            goal.access_rule = lambda state: sum(1 for r in finals if r(state)) >= need
        goal.place_locked_item(WarriorsOrochiItem("Victory", ItemClassification.progression, None, self.player))
        menu.locations.append(goal)

    def create_item(self, name: str) -> WarriorsOrochiItem:
        return WarriorsOrochiItem(name, classification_for(name), ITEM_NAME_TO_ID[name], self.player)

    def create_items(self) -> None:
        chars = self.shuffled_characters()
        self.random.shuffle(chars)
        n_locations = len([loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None])
        names = []  # in priority order: what we would most like to have out in the multiworld first
        if self.options.stage_locks:
            keys = [n for n in STAGE_UNLOCK_NAMES for _ in range(STAGES_PER_STORY - 1)]
            self.random.shuffle(keys)
            names += keys
        names += chars
        if self.options.ability_shuffle:
            names += list(ABILITY_ITEM_NAMES)
        # Ability checks are excluded (filler only), so keep that much room for filler.
        reserve = len(ABILITY_LOCATIONS) if self.options.ability_shuffle else 0
        room = max(0, n_locations - reserve)
        # Anything that does not fit becomes a starting item.
        for name in names[room:]:
            self.multiworld.push_precollected(self.create_item(name))
        pool = [self.create_item(name) for name in names[:room]]
        pool += [self.create_item(self.get_filler_item_name()) for _ in range(n_locations - len(pool))]
        self.multiworld.itempool += pool

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def get_filler_item_name(self) -> str:
        if self.random.randint(1, 100) <= self.options.trap_chance.value:
            return self.random.choice(TRAP_NAMES)
        return FILLER_NAME

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "shuffled_characters": self.shuffled_characters(),
            "gaiden_stage_checks": bool(self.options.gaiden_stage_checks),
            "last_gaiden_checks": bool(self.options.last_gaiden_checks),
            "gaiden_unlock_checks": bool(self.options.gaiden_unlock_checks),
            "show_unlock_messages": bool(self.options.show_unlock_messages),
            "death_link": bool(self.options.death_link),
            "stories_required": self.options.stories_required.value,
            "ko_milestone_max": self.options.ko_milestone_max.value,
            "fourth_weapon_checks": bool(self.options.fourth_weapon_checks),
            "stage_locks": bool(self.options.stage_locks),
            "lock_out_of_logic_stages": bool(self.options.lock_out_of_logic_stages),
            "story_character_requirement": self.options.story_character_requirement.value,
            "ability_shuffle": bool(self.options.ability_shuffle),
            "in_game_notices": bool(self.options.in_game_notices),
        }
