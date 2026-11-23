"""Warriors Orochi client: bridges PCSX2 (via PINE) and an Archipelago server."""
import asyncio
import json
import os
from typing import Dict, Optional, Set

import Utils
from CommonClient import (ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled,
                          handle_url_arg, logger, server_loop)
from NetUtils import ClientStatus

from .data import (CURRENT_STAGE_RECORD, MSG_NEW_OFFICER, MSG_NEW_OFFICER_ORIGINAL, MSG_NEW_SCENARIO,
                   MSG_NEW_SCENARIO_ORIGINAL, MSG_SLOT_LEN, ABILITIES, ABILITIES_IN_USE, ABILITY_LEVELS, ABILITY_NONE, ABILITY_SLOT_EMPTY, CHAR_INDEX, CHAR_UNLOCK_BITS, CHAR_UNLOCK_BYTES, DEFAULT_CHARACTERS, GAIDEN_RECORDS, GAME_NAME,
                   CHAR_RECORD_SIZE, CHAR_RECORDS, GROWTH_POINTS, KO_COUNT, WEAPON_SLOT_SIZE, WEAPON_SLOTS,
                   WEAPON_SLOTS_OFFSET, weapon_id, KO_MILESTONES, PLAYER_HP, PLAYER_MUSOU, PLAYER_UNIT_MARKER, ROSTER, SERIAL, STAGE_RECORD_SIZE, STAGE_RECORDS, STAGE_STATUS_CLEARED, STAGE_STATUS_LOCKED, STAGE_STATUS_OPEN, STORY_RECORDS,
                   STAGE_STATUS_OFFSET, STAGES_PER_STORY, STORIES, STORY_PROGRESS, VANILLA_UNLOCKS)
from .items import FILLER_NAME, ITEM_NAME_TO_ID, TRAP_NAMES, ability_item_name, stage_unlock_name
from .locations import (LOCATION_NAME_TO_ID, ability_location, WEAPON_LOCATIONS, gaiden_location, gaiden_stage_location, ko_location,
                        stage_location, weapon_location)
from .pine import Pine, PineError, bits_to_set, set_to_bits

POLL_SECONDS = 0.5

# Stage record -> the location its clear sends; and which records recruit someone on clear.
RECORD_TO_LOCATION = {rec: LOCATION_NAME_TO_ID[stage_location(s, n)] for (s, n), rec in STORY_RECORDS.items()}
RECORD_TO_LOCATION.update({rec: LOCATION_NAME_TO_ID[gaiden_stage_location(s, n)]
                           for (s, n), rec in GAIDEN_RECORDS.items()})
RECRUIT_RECORDS = {STORY_RECORDS[(u.story, u.stage)] for u in VANILLA_UNLOCKS.values() if u.kind == "stage"}
ID_TO_ITEM = {v: k for k, v in ITEM_NAME_TO_ID.items()}


class WarriorsOrochiCommandProcessor(ClientCommandProcessor):
    def _cmd_pcsx2(self) -> None:
        """Show the PCSX2 connection status."""
        ctx: WarriorsOrochiContext = self.ctx  # type: ignore
        logger.info(f"PCSX2: {ctx.pine_status}")

    def _cmd_roster(self) -> None:
        """List the characters the game currently has unlocked."""
        ctx: WarriorsOrochiContext = self.ctx  # type: ignore
        if ctx.last_bits is None:
            logger.info("Not connected to the game yet.")
            return
        logger.info(", ".join(ROSTER[i] for i in bits_to_set(ctx.last_bits, len(ROSTER))))


class WarriorsOrochiContext(CommonContext):
    game = GAME_NAME
    items_handling = 0b111  # full remote item handling
    command_processor = WarriorsOrochiCommandProcessor

    def __init__(self, server_address: Optional[str], password: Optional[str]):
        super().__init__(server_address, password)
        self.pine = Pine()
        self.pine_status = "not connected"
        self.slot_data: Dict = {}
        self.shuffled: Set[int] = set()      # roster indices the client controls
        self.gaiden_checks = False
        self.last_bits: Optional[bytes] = None
        self.goal_sent = False
        self.applied_filler = 0
        self.applied_traps: Dict[str, int] = {}
        self.suppressed: Set[int] = set()   # stage records we locked that the game had opened
        self.held_abilities: Dict[str, int] = {}  # ability -> level byte the game gave before we had the item
        self.announced = 0
        self.pending_death = False   # a DeathLink arrived; kill the player once in battle
        self.was_alive = False       # player HP was above 0 on the last in-battle tick
        self.link_kill = False       # our current death came from DeathLink: don't echo it
        self.doomed = False          # DeathLink received: HP is held at 1 until the next hit lands
        self.notice_key = None       # (stage record, text) currently written into the game's notices

    # -- server side ------------------------------------------------------------
    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})
            self.shuffled = {CHAR_INDEX[n] for n in self.slot_data.get("shuffled_characters", [])}
            self.gaiden_checks = bool(self.slot_data.get("gaiden_unlock_checks"))
            state = self._load_state()
            self.applied_filler = state.get("applied_filler", 0)
            self.applied_traps = state.get("applied_traps", {})
            self.suppressed = set(state.get("suppressed", []))
            self.held_abilities = state.get("held_abilities", {})
            self.goal_sent = False
            asyncio.create_task(self.update_death_link(bool(self.slot_data.get("death_link"))))
            self.notice_key = None
            # Ask what every one of our checks holds, for the in-game "Sent X to Y" notices.
            asyncio.create_task(self.send_msgs([{"cmd": "LocationScouts", "create_as_hint": 0,
                                                 "locations": sorted(self.server_locations)}]))

    def on_deathlink(self, data: dict) -> None:
        super().on_deathlink(data)
        self.pending_death = True

    def run_gui(self):
        from kvui import GameManager

        class WarriorsOrochiManager(GameManager):
            base_title = "Archipelago Warriors Orochi Client"

        self.ui = WarriorsOrochiManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")

    # -- tiny local save, so filler is never applied twice -------------------------
    def _state_path(self) -> str:
        return Utils.user_path("warriors_orochi", f"{self.seed_name}_{self.team}_{self.slot}.json")

    def _load_state(self) -> dict:
        try:
            with open(self._state_path()) as f:
                return json.load(f)
        except (OSError, ValueError, TypeError):
            return {}

    def _save_state(self) -> None:
        path = self._state_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"applied_filler": self.applied_filler, "applied_traps": self.applied_traps,
                       "suppressed": sorted(self.suppressed), "held_abilities": self.held_abilities}, f)

    # -- game side ----------------------------------------------------------------
    def received_names(self):
        return [ID_TO_ITEM.get(item.item) for item in self.items_received]

    def in_battle(self) -> bool:
        """True while the player's battle unit is live (marker set and a sane max HP)."""
        if self.pine.read32(PLAYER_UNIT_MARKER) != 0xFFFFFFFF:
            return False
        return 0 < self.pine.read16(PLAYER_HP) <= 9999

    async def battle_tick(self, names) -> None:
        """Traps and DeathLink: only touch HP/Musou while a battle is running."""
        if not self.in_battle():
            self.was_alive = False
            self.doomed = False
            if self.pending_death:
                self.pending_death = False   # deaths outside battle are ignored
            return
        hp_addr = PLAYER_HP + 2
        max_hp = self.pine.read16(PLAYER_HP)

        # Received DeathLink. Writing HP = 0 directly soft-locks the game (tested), so drop the
        # player to 1 HP and hold it there: the next hit triggers the game's own defeat.
        if self.pending_death:
            self.pending_death = False
            if self.pine.read16(hp_addr) > 0:
                self.doomed = True
                self.link_kill = True
                logger.info("DeathLink: you are on your last breath. The next hit will finish you!")
        if self.doomed:
            if self.pine.read16(hp_addr) > 1:
                self.pine.write16(hp_addr, 1)

        # Traps, applied one per tick so each one is noticeable.
        for trap in TRAP_NAMES:
            if names.count(trap) > self.applied_traps.get(trap, 0):
                if trap == "Musou Drain Trap":
                    self.pine.write16(PLAYER_MUSOU, 0)
                elif trap == "Low Health Trap":
                    cur = self.pine.read16(hp_addr)
                    self.pine.write16(hp_addr, max(1, min(cur, max_hp // 10)))
                self.applied_traps[trap] = self.applied_traps.get(trap, 0) + 1
                self._save_state()
                logger.info(f"Trap! {trap}")
                break

        # Outgoing DeathLink: HP went from above 0 to 0.
        hp = self.pine.read16(hp_addr)
        if hp == 0 and self.was_alive:
            self.doomed = False
            if self.link_kill:
                self.link_kill = False
            elif "DeathLink" in self.tags:
                await self.send_death(f"{self.player_names.get(self.slot, 'A player')} was defeated in battle.")
        self.was_alive = hp > 0


    def stage_allowed(self, story: str, n: int, names) -> bool:
        """Mirrors WarriorsOrochiWorld.stage_rule: the stage is in logic with what we have."""
        if self.slot_data.get("stage_locks") and names.count(stage_unlock_name(story)) < n - 1:
            return False
        if self.slot_data.get("lock_out_of_logic_stages"):
            pool = [c for c in self.slot_data.get("shuffled_characters", []) if VANILLA_UNLOCKS[c].story == story]
            req = min(self.slot_data.get("story_character_requirement", 4), len(pool))
            need = req * (n - 1) // (STAGES_PER_STORY - 1)
            have = len(set(pool) & set(names))
            if have < need:
                return False
        return True

    def enforce_stage_locks(self, names) -> None:
        """Hide stages that are not in logic yet. The game opens stages itself (status 2); we hide
        the ones not allowed (status 0) and give them back once allowed. Cleared stages (3) are
        never touched."""
        recs = []
        for story in STORIES:
            for n in range(2, STAGES_PER_STORY + 1):
                ok = self.stage_allowed(story, n, names)
                for table in (STORY_RECORDS, GAIDEN_RECORDS):
                    if (story, n) in table:
                        recs.append((table[(story, n)], ok))
        addrs = [STAGE_RECORDS + rec * STAGE_RECORD_SIZE + STAGE_STATUS_OFFSET for rec, _ in recs]
        changed = False
        for (rec, ok), addr, status in zip(recs, addrs, self.pine.read8_many(addrs)):
            if not ok and status == STAGE_STATUS_OPEN:
                self.pine.write8(addr, STAGE_STATUS_LOCKED)
                self.suppressed.add(rec)
                changed = True
            elif ok and rec in self.suppressed:
                if status == STAGE_STATUS_LOCKED:
                    self.pine.write8(addr, STAGE_STATUS_OPEN)
                self.suppressed.discard(rec)
                changed = True
        if changed:
            self._save_state()

    def shuffle_abilities(self, names, new_checks: set) -> None:
        """Earning an ability is a check; it stays hidden until its item arrives."""
        levels = self.pine.read_bytes(ABILITY_LEVELS, len(ABILITIES))
        changed = False
        for i, ability in enumerate(ABILITIES):
            level = levels[i]
            have = ability_item_name(ability) in names
            if level != ABILITY_NONE:
                new_checks.add(LOCATION_NAME_TO_ID[ability_location(ability)])
            if not have and level != ABILITY_NONE:
                # The game just gave it to us: remember its level and hide it.
                self.held_abilities[ability] = max(self.held_abilities.get(ability, 0), level)
                self.pine.write8(ABILITY_LEVELS + i, ABILITY_NONE)
                changed = True
            elif have and level == ABILITY_NONE:
                self.pine.write8(ABILITY_LEVELS + i, self.held_abilities.pop(ability, 0))
                changed = True
        if changed:
            self._save_state()
            # Unequip anything we just hid, so no slot points at an ability the game thinks we lack.
            levels = self.pine.read_bytes(ABILITY_LEVELS, len(ABILITIES))
            slots = bytearray(self.pine.read_bytes(ABILITIES_IN_USE, 7))
            for k, ab in enumerate(slots):
                if ab < len(ABILITIES) and levels[ab] == ABILITY_NONE:
                    slots[k] = ABILITY_SLOT_EMPTY
            self.pine.write_bytes(ABILITIES_IN_USE, bytes(slots))

    # -- in-game notices -----------------------------------------------------------
    def notice_text(self, location_id: int) -> Optional[str]:
        """'Sent [01Hookshot] to Alex!' for the item on a check, trimmed to fit the game's text slot."""
        info = self.locations_info.get(location_id)
        if info is None:
            return None
        item = self.item_names.lookup_in_slot(info.item, info.player)
        if info.player == self.slot:
            head, tail = "Found ", "!"
        else:
            head, tail = "Sent ", f" to {self.player_names.get(info.player, 'someone')}!"
        room = MSG_SLOT_LEN - len(head) - len(tail) - 4   # 4 = "[01" + "]"
        if room < 6:                                          # very long player name: drop it
            tail, room = "!", MSG_SLOT_LEN - len(head) - 5
        if len(item) > room:
            item = item[:room - 2] + ".."
        return f"{head}[01{item}]{tail}"

    def write_notice(self, addr: int, text: str) -> None:
        data = text.encode("ascii", "replace")[:MSG_SLOT_LEN] + b"\0"
        self.pine.write_bytes(addr, data)

    def update_notices(self) -> None:
        """During a battle, put that stage's check item into the game's end-of-stage notices."""
        # Only change text while a battle runs: the notices show after it ends, so leave them alone then.
        if not self.in_battle():
            return
        rec = self.pine.read8(CURRENT_STAGE_RECORD)
        loc = RECORD_TO_LOCATION.get(rec)
        text = self.notice_text(loc) if loc is not None and loc not in self.checked_locations else None
        key = (rec, text)
        if key == self.notice_key:
            return
        if text is None:
            self.write_notice(MSG_NEW_OFFICER, MSG_NEW_OFFICER_ORIGINAL)
            self.write_notice(MSG_NEW_SCENARIO, MSG_NEW_SCENARIO_ORIGINAL)
        elif rec in RECRUIT_RECORDS:   # the stage recruits someone: the "new officer" notice will show
            self.write_notice(MSG_NEW_OFFICER, text)
            self.write_notice(MSG_NEW_SCENARIO, MSG_NEW_SCENARIO_ORIGINAL)
        else:
            self.write_notice(MSG_NEW_OFFICER, MSG_NEW_OFFICER_ORIGINAL)
            self.write_notice(MSG_NEW_SCENARIO, text)
        self.notice_key = key

    async def game_tick(self) -> None:
        names = self.received_names()

        # 1. Character roster: the game owns non-shuffled bits, the server owns shuffled ones.
        bits = self.pine.read_bytes(CHAR_UNLOCK_BITS, CHAR_UNLOCK_BYTES)
        current = set(bits_to_set(bits, len(ROSTER)))
        received = {CHAR_INDEX[n] for n in names if n in CHAR_INDEX}
        new_checks = set()

        if self.gaiden_checks:
            # A shuffled Gaiden character the server has not given us just appeared:
            # the player completed that Gaiden objective.
            for idx in (current & self.shuffled) - received:
                loc = LOCATION_NAME_TO_ID.get(gaiden_location(ROSTER[idx]))
                if loc is not None:
                    new_checks.add(loc)

        desired = (current - self.shuffled) | {CHAR_INDEX[n] for n in DEFAULT_CHARACTERS} | received
        if desired != current:
            self.pine.write_bytes(CHAR_UNLOCK_BITS, set_to_bits(desired, CHAR_UNLOCK_BYTES))
        self.last_bits = set_to_bits(desired, CHAR_UNLOCK_BYTES)

        # 1b. Real stage locks.
        if self.slot_data.get("stage_locks") or self.slot_data.get("lock_out_of_logic_stages"):
            self.enforce_stage_locks(names)

        # 2. Story progress -> stage clear checks.
        stories_done = 0
        for story in STORIES:
            addr = STORY_PROGRESS.get(story)
            if addr is None:
                continue
            progress = min(self.pine.read8(addr), STAGES_PER_STORY)
            for n in range(1, progress + 1):
                new_checks.add(LOCATION_NAME_TO_ID[stage_location(story, n)])
            stories_done += progress >= STAGES_PER_STORY

        # 2b. Gaiden stage clears: status byte of that stage's record.
        if self.slot_data.get("gaiden_stage_checks"):
            for (story, n), rec in GAIDEN_RECORDS.items():
                if n == 8 and not self.slot_data.get("last_gaiden_checks"):
                    continue
                status = self.pine.read8(STAGE_RECORDS + rec * STAGE_RECORD_SIZE + STAGE_STATUS_OFFSET)
                if status >= STAGE_STATUS_CLEARED:
                    new_checks.add(LOCATION_NAME_TO_ID[gaiden_stage_location(story, n)])

        # 2a. Ability shuffle.
        if self.slot_data.get("ability_shuffle"):
            self.shuffle_abilities(names, new_checks)

        # 2b2. 4th weapons, read from every character's weapon slots.
        if self.slot_data.get("fourth_weapon_checks"):
            chars = [c for c in WEAPON_LOCATIONS.values()
                     if LOCATION_NAME_TO_ID[weapon_location(c)] not in self.checked_locations]
            addrs = [CHAR_RECORDS + CHAR_INDEX[c] * CHAR_RECORD_SIZE + WEAPON_SLOTS_OFFSET + s * WEAPON_SLOT_SIZE
                     for c in chars for s in range(WEAPON_SLOTS)]
            ids = self.pine.read16_many(addrs)
            for i, c in enumerate(chars):
                if weapon_id(CHAR_INDEX[c], 4) in ids[i * WEAPON_SLOTS:(i + 1) * WEAPON_SLOTS]:
                    new_checks.add(LOCATION_NAME_TO_ID[weapon_location(c)])

        # 2c. KO milestones (the counter is per battle and resets at camp).
        ko_max = self.slot_data.get("ko_milestone_max", 0)
        if ko_max:
            kos = self.pine.read32(KO_COUNT)
            new_checks |= {LOCATION_NAME_TO_ID[ko_location(c)] for c in KO_MILESTONES if c <= ko_max and kos >= c}

        new_checks -= self.checked_locations
        if new_checks:
            await self.check_locations(new_checks)

        # 3. Filler: growth points.
        filler = names.count(FILLER_NAME)
        if filler > self.applied_filler:
            gp = self.pine.read32(GROWTH_POINTS)
            self.pine.write32(GROWTH_POINTS, min(gp + 1000 * (filler - self.applied_filler), 9_999_999))
            self.applied_filler = filler
            self._save_state()

        # 3a. In-game "Sent X to Y" notices.
        if self.slot_data.get("in_game_notices", True):
            self.update_notices()

        # 3b. Battle-only effects.
        await self.battle_tick(names)

        # 4. Messages for newly received characters.
        if self.slot_data.get("show_unlock_messages", True) and len(names) > self.announced:
            for n in names[self.announced:]:
                if n in CHAR_INDEX:
                    story = VANILLA_UNLOCKS[n].story if n in VANILLA_UNLOCKS else None
                    where = f" (usable in Free Mode and the {story} story)" if story else ""
                    logger.info(f"{n} has joined your army!{where}")
            self.announced = len(names)

        # 5. Goal: enough stories cleared. Zuo Ci is the game's own "all stories cleared" reward,
        #    so his bit is a fallback when all four are required.
        need = self.slot_data.get("stories_required", len(STORIES))
        zuo_ci = need >= len(STORIES) and CHAR_INDEX["Zuo Ci"] in current
        if not self.goal_sent and (stories_done >= need or zuo_ci):
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            self.goal_sent = True


async def game_loop(ctx: WarriorsOrochiContext) -> None:
    while not ctx.exit_event.is_set():
        try:
            if not ctx.pine.connected:
                ctx.pine.connect()
            if ctx.pine_status != "connected":
                game = ctx.pine.game_id()
                if game.replace("_", "-").replace(".", "") != SERIAL:
                    ctx.pine_status = f"wrong game loaded ({game!r}); expected {SERIAL}"
                    ctx.pine.close()
                    await asyncio.sleep(5)
                    continue
                ctx.pine_status = "connected"
                logger.info("Connected to PCSX2.")
            if ctx.slot is not None and ctx.slot_data:
                await ctx.game_tick()
            # PCSX2's PINE serves one connection at a time; let go so other tools can use it too.
            ctx.pine.close()
        except (OSError, PineError) as e:
            if ctx.pine_status == "connected":
                logger.info(f"Lost PCSX2 connection: {e}")
            ctx.pine_status = "waiting for PCSX2 (enable PINE, slot 28011, and load the game)"
            ctx.pine.close()
            await asyncio.sleep(3)
            continue
        await asyncio.sleep(POLL_SECONDS)


def launch(*args: str) -> None:
    async def main(parsed):
        ctx = WarriorsOrochiContext(parsed.connect, parsed.password)
        ctx.auth = getattr(parsed, "name", None)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        loop_task = asyncio.create_task(game_loop(ctx), name="Warriors Orochi game loop")
        await ctx.exit_event.wait()
        loop_task.cancel()
        ctx.pine.close()
        await ctx.shutdown()

    import colorama
    parser = get_base_parser(description="Warriors Orochi Archipelago client")
    parser.add_argument("--name", default=None, help="Slot name to connect as.")
    parser.add_argument("url", nargs="?", help="Archipelago connection url")
    parsed = handle_url_arg(parser.parse_args(args), parser=parser)
    Utils.init_logging("WarriorsOrochiClient")
    colorama.just_fix_windows_console()
    asyncio.run(main(parsed))
    colorama.deinit()
