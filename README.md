# Warriors Orochi (PS2) for Archipelago

An [Archipelago](https://archipelago.gg) multiworld randomizer for **Warriors Orochi** (PS2, NTSC-U, SLUS-21662),
played on **PCSX2** (tested on v2.8.2). The client talks to PCSX2 over its built-in PINE interface: no patching of the game.

## What gets randomized
- **Characters** are the main items. Officers who would normally join after a stage are spread across the multiworld.
  In Story Mode a character can only be fielded in the story that normally recruits them, and the logic knows this.
- **Checks:** clearing every story stage (32), Gaiden stages 2-7 (24, on by default), and optionally:
  Last Gaiden stages, Gaiden unlock objectives, KO milestones in one battle, every character's 4th weapon,
  and earning each of the 18 abilities.

## Options (highlights)
| Option | What it does |
|---|---|
| `stories_required` | Clear 1-4 stories to win (default 4) |
| `story_character_requirement` | How many of a story's characters logic expects before its final stage |
| `stage_locks` | Really locks stages behind "Progressive <Story> Stage" items (works in Story and Free Mode) |
| `ability_shuffle` | Abilities stay hidden until their item arrives |
| `fourth_weapon_checks` | A check for each character's 4th weapon |
| `ko_milestone_max` | Checks for 100 / 200 / 300 / 500 / 750 / 1000 KOs in a battle |
| `trap_chance` | Musou Drain and Low Health traps |
| `in_game_notices` | The game's own end-of-stage notice says what you found, e.g. "Sent Hookshot to Alex!" (on by default) |
| `death_link` | Supported (a received death leaves you at 1 HP; the next hit finishes you) |

Full details: [game page](worlds/warriors_orochi/docs/en_Warriors%20Orochi.md) and
[setup guide](worlds/warriors_orochi/docs/setup_en.md).

## Install
1. Download `warriors_orochi.apworld` from the [latest release](../../releases/latest) and double-click it
   (or drop it into Archipelago's `custom_worlds` folder). Needs Archipelago 0.6.7 or newer.
2. In PCSX2: Settings → Advanced → enable **PINE** on slot **28011**.
3. Generate as usual, then open **Warriors Orochi Client** from the Archipelago Launcher.

## Tracker
A PopTracker pack with Archipelago autotracking is attached to each release
(`warriors_orochi_poptracker.zip`). It is built from the world's own tables by `tools/make_poptracker.py`.

## Repository layout
- `worlds/warriors_orochi/` – the apworld (world, client, PINE bridge, docs, tests)
- `tools/` – memory probe, CodeBreaker decryptor, PopTracker pack builder
- `cheats/` – optional PCSX2 testing cheats (Attack 5000, infinite health/musou/time)
- `docs/memory_map.md` – everything known about the game's memory

## Known limitations
- Personal items are not randomized yet (their save flag has not been found).
- Earn Ability checks only hold filler, because the game's exact ability conditions are not mapped yet.

Run the tests from an Archipelago source checkout: `python -m pytest worlds/warriors_orochi/test`.
