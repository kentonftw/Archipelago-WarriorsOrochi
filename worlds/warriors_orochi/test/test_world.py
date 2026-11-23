from ..data import CHAR_INDEX, DEFAULT_CHARACTERS, GAIDEN_RECORDS, ROSTER, STORY_RECORDS, VANILLA_UNLOCKS
from ..items import FILLER_NAME, ITEM_GROUPS, TRAP_NAMES
from ..pine import bits_to_set, set_to_bits
from . import WarriorsOrochiTestBase


class TestDefaults(WarriorsOrochiTestBase):
    def test_location_count(self) -> None:
        locs = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locs), 32 + 24)  # story stages + Gaiden 2-7

    def test_pool_has_every_stage_character_and_filler(self) -> None:
        names = [item.name for item in self.multiworld.itempool]
        stage_chars = [n for n, u in VANILLA_UNLOCKS.items() if u.kind == "stage"]
        for n in stage_chars:
            self.assertIn(n, names)
        self.assertEqual(names.count(FILLER_NAME), 56 - len(stage_chars))

    def test_first_stages_open(self) -> None:
        for story in ("Shu", "Wei", "Wu", "Samurai"):
            self.assertTrue(self.can_reach_location(f"{story} Stage 1 Cleared"))
            self.assertTrue(self.can_reach_location(f"{story} Stage 2 Cleared"))

    def test_final_stage_needs_own_story_characters(self) -> None:
        self.assertFalse(self.can_reach_location("Shu Stage 8 Cleared"))
        pool = {item.name for item in self.multiworld.itempool}
        wei = sorted(ITEM_GROUPS["Wei Characters"] & pool)[:4]
        self.collect_by_name(wei)
        self.assertFalse(self.can_reach_location("Shu Stage 8 Cleared"),
                         "Wei characters must not count for the Shu story")
        shu = sorted(ITEM_GROUPS["Shu Characters"] & pool)[:4]
        self.collect_by_name(shu)
        self.assertTrue(self.can_reach_location("Shu Stage 8 Cleared"))


class TestNoRequirements(WarriorsOrochiTestBase):
    options = {"story_character_requirement": 0}

    def test_everything_open(self) -> None:
        for loc in self.multiworld.get_locations(self.player):
            self.assertTrue(loc.can_reach(self.multiworld.state), loc.name)


class TestGaidenUnlocks(WarriorsOrochiTestBase):
    options = {"gaiden_unlock_checks": True}

    def test_counts(self) -> None:
        locs = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        gaiden_chars = [n for n, u in VANILLA_UNLOCKS.items() if u.kind == "gaiden"]
        self.assertEqual(len(locs), 32 + 24 + len(gaiden_chars))


class TestNoGaidenStages(WarriorsOrochiTestBase):
    options = {"gaiden_stage_checks": False}

    def test_surplus_characters_become_starting_items(self) -> None:
        locs = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locs), 32)
        start = [i.name for i in self.multiworld.precollected_items[self.player]]
        stage_chars = [n for n, u in VANILLA_UNLOCKS.items() if u.kind == "stage"]
        self.assertEqual(len(start), len(stage_chars) - 32)


class TestData(WarriorsOrochiTestBase):
    run_default_tests = False

    def test_roster_consistency(self) -> None:
        self.assertEqual(len(ROSTER), 79)
        self.assertEqual(len(DEFAULT_CHARACTERS), 12)
        records = list(GAIDEN_RECORDS.values()) + list(STORY_RECORDS.values())
        self.assertEqual(len(records), len(set(records)), "a stage record is mapped twice")
        self.assertTrue(all(0 <= r < 60 for r in records))
        self.assertEqual(len(records), 60, "every stage should be mapped")

    def test_bit_helpers_round_trip(self) -> None:
        live = bytes.fromhex("0100401001460ca28801")  # real RAM after Shu Stage 2
        on = bits_to_set(live, 79)
        self.assertIn(CHAR_INDEX["Yue Ying"], on)
        self.assertIn(CHAR_INDEX["Saika Magoichi"], on)
        self.assertEqual(set_to_bits(on, 10), live)


class TestLastGaiden(WarriorsOrochiTestBase):
    options = {"last_gaiden_checks": True}

    def test_counts(self) -> None:
        locs = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locs), 32 + 28)
        self.assertIn("Samurai Gaiden 8 Cleared", [loc.name for loc in locs])


def _goal_reachable(test) -> bool:
    return test.multiworld.state.can_reach_location("Stories Cleared", test.player)


class TestGoalAllStories(WarriorsOrochiTestBase):
    def test_one_story_is_not_enough(self) -> None:
        pool = {item.name for item in self.multiworld.itempool}
        self.collect_by_name(sorted(ITEM_GROUPS["Shu Characters"] & pool)[:4])
        self.assertFalse(_goal_reachable(self))
        for story in ("Wei", "Wu", "Samurai"):
            self.collect_by_name(sorted(ITEM_GROUPS[f"{story} Characters"] & pool)[:4])
        self.assertTrue(_goal_reachable(self))


class TestGoalOneStory(WarriorsOrochiTestBase):
    options = {"stories_required": 1}

    def test_any_one_story(self) -> None:
        self.assertFalse(_goal_reachable(self))
        pool = {item.name for item in self.multiworld.itempool}
        self.collect_by_name(sorted(ITEM_GROUPS["Wu Characters"] & pool)[:4])
        self.assertTrue(_goal_reachable(self))
        self.assertEqual(self.world.fill_slot_data()["stories_required"], 1)


class TestKOMilestones(WarriorsOrochiTestBase):
    options = {"ko_milestone_max": 1000}

    def test_counts_and_logic(self) -> None:
        names = [loc.name for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(names), 32 + 24 + 6)
        self.assertTrue(self.can_reach_location("300 KOs in One Battle"))
        self.assertFalse(self.can_reach_location("500 KOs in One Battle"))
        pool = {item.name for item in self.multiworld.itempool}
        self.collect_by_name(sorted(ITEM_GROUPS["Samurai Characters"] & pool)[:2])
        self.assertTrue(self.can_reach_location("1000 KOs in One Battle"))


class TestKOMilestonesPartial(WarriorsOrochiTestBase):
    options = {"ko_milestone_max": 300}

    def test_counts(self) -> None:
        names = [loc.name for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertIn("300 KOs in One Battle", names)
        self.assertNotIn("500 KOs in One Battle", names)


class TestAllTraps(WarriorsOrochiTestBase):
    options = {"trap_chance": 100, "death_link": True}

    def test_filler_is_traps(self) -> None:
        names = [item.name for item in self.multiworld.itempool]
        self.assertNotIn(FILLER_NAME, names)
        self.assertTrue(any(n in TRAP_NAMES for n in names))
        self.assertTrue(self.world.fill_slot_data()["death_link"])


class TestFourthWeapons(WarriorsOrochiTestBase):
    options = {"fourth_weapon_checks": True}

    def test_counts_and_logic(self) -> None:
        names = [loc.name for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(names), 32 + 24 + 74)
        self.assertNotIn("Orochi's 4th Weapon", names)
        # Default character: only needs the Hard 3-star stages (a Stage 5 somewhere).
        self.assertFalse(self.can_reach_location("Zhao Yun's 4th Weapon"))
        pool = {item.name for item in self.multiworld.itempool}
        self.collect_by_name(sorted(ITEM_GROUPS["Wei Characters"] & pool)[:2])
        self.assertTrue(self.can_reach_location("Zhao Yun's 4th Weapon"))
        # Shuffled character: needs the character itself too.
        self.assertFalse(self.can_reach_location("Okuni's 4th Weapon"))
        self.collect_by_name(["Okuni"])
        self.assertTrue(self.can_reach_location("Okuni's 4th Weapon"))

    def test_weapon_id_formula(self) -> None:
        from ..data import weapon_id
        self.assertEqual(weapon_id(CHAR_INDEX["Toyotomi Hideyoshi"], 1), 252)  # seen in RAM


class TestStageLocks(WarriorsOrochiTestBase):
    options = {"stage_locks": True, "story_character_requirement": 0}

    def test_items_gate_stages(self) -> None:
        names = [item.name for item in self.multiworld.itempool]
        self.assertEqual(names.count("Progressive Shu Stage"), 7)
        self.assertTrue(self.can_reach_location("Shu Stage 1 Cleared"))
        self.assertFalse(self.can_reach_location("Shu Stage 2 Cleared"))
        self.assertFalse(self.can_reach_location("Shu Gaiden 2 Cleared"))
        self.collect(self.get_item_by_name("Progressive Shu Stage"))
        self.assertTrue(self.can_reach_location("Shu Stage 2 Cleared"))
        self.assertTrue(self.can_reach_location("Shu Gaiden 2 Cleared"))
        self.assertFalse(self.can_reach_location("Shu Stage 3 Cleared"))
        self.assertFalse(self.can_reach_location("Wei Stage 2 Cleared"))
        self.assertTrue(self.world.fill_slot_data()["stage_locks"])


class TestAbilityShuffle(WarriorsOrochiTestBase):
    options = {"ability_shuffle": True}

    def test_counts_and_exclusion(self) -> None:
        from BaseClasses import LocationProgressType
        locs = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locs), 32 + 24 + 18)
        names = [item.name for item in self.multiworld.itempool]
        self.assertIn("Ability: Speed", names)
        speed = self.multiworld.get_location("Earn Ability: Speed", self.player)
        self.assertEqual(speed.progress_type, LocationProgressType.EXCLUDED)
