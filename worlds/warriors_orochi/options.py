from dataclasses import dataclass

from Options import DefaultOnToggle, PerGameCommonOptions, Range, StartInventoryPool, Toggle


class GaidenStageChecks(DefaultOnToggle):
    """
    Adds a check for clearing each Gaiden stage (Gaiden 2-7 of every story, 24 checks).
    Gaiden stages open as you clear the matching story chapter.
    """
    display_name = "Gaiden Stage Checks"


class LastGaidenChecks(Toggle):
    """
    Adds checks for the four Gaiden 8 ("Last Gaiden") stages. Each one only opens after a special
    objective in that story's Chapter 7 (e.g. Samurai: 1,000 KOs), so these are hard to reach.
    Requires Gaiden Stage Checks.
    """
    display_name = "Last Gaiden Checks"


class GaidenUnlockChecks(Toggle):
    """
    Adds a check for every character whose vanilla unlock is a Gaiden (X-stage) objective,
    e.g. "Shu Gaiden 2: initiate Jiang Wei's ambush plan". Those characters are then shuffled too.
    These objectives can be fiddly; leave this off for a shorter, easier seed.
    """
    display_name = "Gaiden Unlock Checks"


class StoryCharacterRequirement(Range):
    """
    Logic only. In Story Mode you can only field characters recruited by that story, so each
    story's stages are gated by that story's own characters. This is how many of them you are
    expected to have before its final stage (Stage 8); earlier stages scale up linearly.
    0 means no character requirements at all.
    """
    display_name = "Story Character Requirement"
    range_start = 0
    range_end = 8
    default = 4


class StoriesRequired(Range):
    """
    How many of the four stories (Shu, Wei, Wu, Samurai) you must clear (Stage 8) to finish.
    Lower this for a shorter seed.
    """
    display_name = "Stories Required"
    range_start = 1
    range_end = 4
    default = 4


class KOMilestoneMax(Range):
    """
    Adds checks for getting a number of KOs in a single battle: 100, 200, 300, 500, 750 and 1000,
    up to this value. 0 turns KO checks off. 500 KOs and above are only expected once you can reach
    a Stage 5 in some story.
    """
    display_name = "KO Milestone Checks"
    range_start = 0
    range_end = 1000
    default = 0


class TrapChance(Range):
    """
    Percent chance for each filler item to be a trap instead: Musou Drain (empties your Musou gauge)
    or Low Health (drops you to 10% health). Traps wait until you are in a battle.
    """
    display_name = "Trap Chance"
    range_start = 0
    range_end = 100
    default = 0


class FourthWeaponChecks(Toggle):
    """
    Adds a check for getting each character's 4th (strongest) weapon. In vanilla these drop on
    Hard difficulty in 3-star or harder stages. Counted when the weapon is saved, i.e. back at camp.
    The character has to be on your team, so this needs that character first. Adds about 74 checks.
    """
    display_name = "4th Weapon Checks"


class StageLocks(Toggle):
    """
    Really locks story stages. Each story gets 7 "Progressive <Story> Stage" items; stage N (and
    Gaiden N) only opens once you have N-1 of that story's items AND have cleared the stage before it.
    Stage 1 of every story is always open. Without this, later stages are only "out of logic".
    """
    display_name = "Stage Locks"


class AbilityShuffle(Toggle):
    """
    Shuffles the 18 army-wide abilities (Vitality, Speed, Karma, ...). Earning an ability in-game
    is a check; you can only see and equip it once its "Ability: <name>" item arrives (any levels
    earned meanwhile are kept). How the game hands out abilities is not fully mapped yet, so
    these checks only ever hold filler, never anything you need.
    """
    display_name = "Ability Shuffle"


class DeathLink(Toggle):
    """
    When you die, everyone dies. Of course the reverse is true too.
    A received death drops you to 1 health in battle; the next hit finishes you. Do not use with an Infinite Health cheat.
    """
    display_name = "Death Link"


class ShowUnlockMessages(DefaultOnToggle):
    """Print received characters in the client window."""
    display_name = "Show Unlock Messages"


@dataclass
class WarriorsOrochiOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    gaiden_stage_checks: GaidenStageChecks
    last_gaiden_checks: LastGaidenChecks
    gaiden_unlock_checks: GaidenUnlockChecks
    story_character_requirement: StoryCharacterRequirement
    stories_required: StoriesRequired
    ko_milestone_max: KOMilestoneMax
    trap_chance: TrapChance
    fourth_weapon_checks: FourthWeaponChecks
    stage_locks: StageLocks
    ability_shuffle: AbilityShuffle
    show_unlock_messages: ShowUnlockMessages
    death_link: DeathLink
