"""Builds the Warriors Orochi PopTracker pack from the apworld's own data tables.

Run from an Archipelago source checkout that has worlds/warriors_orochi installed:
    python make_poptracker.py <output_dir>
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

from worlds.warriors_orochi.data import (ABILITIES, CHAR_INDEX, GAIDEN_RECORDS, KO_MILESTONES, STAGES_PER_STORY,
                                         STORIES, VANILLA_UNLOCKS)
from worlds.warriors_orochi.items import (ABILITY_ITEM_NAMES, FILLER_NAME, GAIDEN_CHARACTERS, ITEM_NAME_TO_ID,
                                          STAGE_CHARACTERS, STAGE_UNLOCK_NAMES, TRAP_NAMES, stage_unlock_name)
from worlds.warriors_orochi.locations import (ABILITY_LOCATIONS, GAIDEN_LOCATIONS, KO_LOCATIONS,
                                              LOCATION_NAME_TO_ID, WEAPON_LOCATIONS, ability_location,
                                              gaiden_location, gaiden_stage_location, ko_location, stage_location,
                                              weapon_location)

VERSION = json.load(open(os.path.join(os.path.dirname(__import__("worlds.warriors_orochi").warriors_orochi.__file__),
                                      "archipelago.json")))["world_version"]
ABBREV = {"Recuperate": "RCP", "Recover": "RCV", "Refill": "RFL"}
COLORS = {"Shu": (46, 139, 87), "Wei": (40, 90, 180), "Wu": (190, 50, 50), "Samurai": (200, 140, 30),
          "Ability": (110, 70, 160), "Key": (90, 90, 90)}


def code(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")


def font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def badge(path, text, color, size=48):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=8, fill=color + (255,), outline=(255, 255, 255, 255), width=2)
    f = font(15 if len(text) <= 3 else 12)
    w, h = d.textbbox((0, 0), text, font=f)[2:]
    d.text(((size - w) / 2, (size - h) / 2 - 1), text, font=f, fill=(255, 255, 255, 255))
    img.save(path)


def initials(name: str) -> str:
    parts = name.replace("-", " ").split()
    return (parts[0][:2] if len(parts) == 1 else parts[0][0] + parts[-1][0]).upper() if parts else "?"


def main(out: str) -> None:
    for sub in ("images/items", "items", "locations", "maps", "layouts", "scripts"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    characters = [n for n in CHAR_INDEX if n in STAGE_CHARACTERS or n in GAIDEN_CHARACTERS]

    # ---------------------------------------------------------------- items
    items, item_map = [], {}
    for name in characters:
        story = VANILLA_UNLOCKS[name].story
        img = f"images/items/{code(name)}.png"
        badge(os.path.join(out, img), initials(name), COLORS[story])
        items.append({"name": name, "type": "toggle", "img": img, "codes": code(name)})
        item_map[ITEM_NAME_TO_ID[name]] = [code(name), "toggle"]
    for story, name in zip(STORIES, STAGE_UNLOCK_NAMES):
        img = f"images/items/{code(name)}.png"
        badge(os.path.join(out, img), story[:2].upper(), COLORS[story])
        items.append({"name": name, "type": "consumable", "img": img, "codes": code(name),
                      "max_quantity": STAGES_PER_STORY - 1, "min_quantity": 0})
        item_map[ITEM_NAME_TO_ID[name]] = [code(name), "consumable"]
    for ability, name in zip(ABILITIES, ABILITY_ITEM_NAMES):
        img = f"images/items/{code(name)}.png"
        badge(os.path.join(out, img), ABBREV.get(ability, ability[:3].upper()), COLORS["Ability"])
        items.append({"name": name, "type": "toggle", "img": img, "codes": code(name)})
        item_map[ITEM_NAME_TO_ID[name]] = [code(name), "toggle"]
    # Hidden option flags, set from slot_data so sections can show or hide.
    flags = ["opt_gaiden_stages", "opt_last_gaiden", "opt_gaiden_unlocks", "opt_weapons", "opt_abilities"]
    flags += [f"opt_ko_{c}" for c in KO_MILESTONES]
    badge(os.path.join(out, "images/items/flag.png"), "OPT", COLORS["Key"], 24)
    for f in flags:
        items.append({"name": f, "type": "toggle", "img": "images/items/flag.png", "codes": f})
    json.dump(items, open(os.path.join(out, "items/items.json"), "w"), indent=1)

    # ---------------------------------------------------------------- map
    W, H = 1000, 640
    img = Image.new("RGB", (W, H), (28, 24, 40))
    d = ImageDraw.Draw(img)
    regions = {}
    col_w = W // 4
    for i, story in enumerate(STORIES):
        x0 = i * col_w
        d.rectangle([x0 + 6, 6, x0 + col_w - 6, 370], outline=COLORS[story], width=3)
        d.text((x0 + 16, 12), f"{story} Story", font=font(20), fill=COLORS[story])
        regions[story] = (x0 + col_w // 2, 200)
    extras = [("KO Milestones", 125), ("4th Weapons", 375), ("Abilities", 625), ("Gaiden Unlocks", 875)]
    for name, cx in extras:
        d.rectangle([cx - 119, 386, cx + 119, 630], outline=(180, 180, 180), width=2)
        d.text((cx - 105, 392), name, font=font(18), fill=(220, 220, 220))
        regions[name] = (cx, 520)
    img.save(os.path.join(out, "images/map.png"))
    json.dump([{"name": "Warriors Orochi", "img": "images/map.png", "location_size": 40,
                "location_border_thickness": 3}], open(os.path.join(out, "maps/maps.json"), "w"), indent=1)

    # ---------------------------------------------------------------- locations
    loc_map, locations = {}, []

    def place(region, sections):
        x, y = regions[region]
        locations.append({"name": region, "map_locations": [{"map": "Warriors Orochi", "x": x, "y": y}],
                          "sections": sections})

    for story in STORIES:
        sections = []
        for n in range(1, STAGES_PER_STORY + 1):
            sec = f"Stage {n}"
            sections.append({"name": sec, "access_rules": [f"$stage|{story}|{n}"]})
            loc_map[LOCATION_NAME_TO_ID[stage_location(story, n)]] = f"@{story}/{sec}"
        for n in range(2, STAGES_PER_STORY + 1):
            if (story, n) not in GAIDEN_RECORDS:
                continue
            sec = f"Gaiden {n}"
            vis = ["opt_gaiden_stages,opt_last_gaiden"] if n == STAGES_PER_STORY else ["opt_gaiden_stages"]
            sections.append({"name": sec, "access_rules": [f"$stage|{story}|{n}"], "visibility_rules": vis})
            loc_map[LOCATION_NAME_TO_ID[gaiden_stage_location(story, n)]] = f"@{story}/{sec}"
        place(story, sections)

    sections = []
    for c in KO_MILESTONES:
        sec = f"{c} KOs"
        rule = "$hard" if c >= 500 else ""
        sections.append({"name": sec, "access_rules": [rule] if rule else [], "visibility_rules": [f"opt_ko_{c}"]})
        loc_map[LOCATION_NAME_TO_ID[ko_location(c)]] = f"@KO Milestones/{sec}"
    place("KO Milestones", sections)

    sections = []
    for char in WEAPON_LOCATIONS.values():
        sections.append({"name": char, "access_rules": [f"$weapon|{code(char)}"], "visibility_rules": ["opt_weapons"]})
        loc_map[LOCATION_NAME_TO_ID[weapon_location(char)]] = f"@4th Weapons/{char}"
    place("4th Weapons", sections)

    sections = []
    for ability in ABILITIES:
        sections.append({"name": ability, "visibility_rules": ["opt_abilities"]})
        loc_map[LOCATION_NAME_TO_ID[ability_location(ability)]] = f"@Abilities/{ability}"
    place("Abilities", sections)

    sections = []
    for loc_name, char in GAIDEN_LOCATIONS.items():
        u = VANILLA_UNLOCKS[char]
        sections.append({"name": loc_name, "access_rules": [f"$stage|{u.story}|{u.stage}"],
                         "visibility_rules": ["opt_gaiden_unlocks"]})
        loc_map[LOCATION_NAME_TO_ID[loc_name]] = f"@Gaiden Unlocks/{loc_name}"
    place("Gaiden Unlocks", sections)
    json.dump(locations, open(os.path.join(out, "locations/locations.json"), "w"), indent=1)

    # ---------------------------------------------------------------- layouts
    def grid(codes, per_row=8):
        return [codes[i:i + per_row] for i in range(0, len(codes), per_row)]

    groups = []
    for story in STORIES:
        codes = [code(n) for n in characters if VANILLA_UNLOCKS[n].story == story]
        groups.append({"type": "group", "header": f"{story} Characters",
                       "content": {"type": "itemgrid", "item_margin": "1", "item_size": 32, "rows": grid(codes)}})
    groups.append({"type": "group", "header": "Stage Unlocks",
                   "content": {"type": "itemgrid", "item_size": 32, "rows": [[code(n) for n in STAGE_UNLOCK_NAMES]]}})
    groups.append({"type": "group", "header": "Abilities",
                   "content": {"type": "itemgrid", "item_margin": "1", "item_size": 32,
                               "rows": grid([code(n) for n in ABILITY_ITEM_NAMES], 6)}})
    items_panel = {"type": "array", "orientation": "vertical", "margin": "0,0,3,0", "content": groups}
    layouts = {
        "items_panel": items_panel,
        "tracker_default": {"type": "container", "background": "#00000000", "content": {
            "type": "dock", "dock": "left", "content": [
                {"type": "dock", "dock": "left", "content": {"type": "layout", "key": "items_panel"}},
                {"type": "map", "maps": ["Warriors Orochi"]}]}},
        "tracker_broadcast": {"type": "array", "orientation": "vertical", "content": {"type": "layout", "key": "items_panel"}},
    }
    json.dump(layouts, open(os.path.join(out, "layouts/tracker.json"), "w"), indent=1)

    # ---------------------------------------------------------------- scripts
    story_of = {code(n): VANILLA_UNLOCKS[n].story for n in characters}
    weapon_char = {code(c): (code(c) if c in characters else None, VANILLA_UNLOCKS[c].story if c in VANILLA_UNLOCKS else None,
                             VANILLA_UNLOCKS[c].stage if c in VANILLA_UNLOCKS else 0)
                   for c in WEAPON_LOCATIONS.values()}
    with open(os.path.join(out, "scripts/data.lua"), "w") as f:
        f.write("-- generated by tools/make_poptracker.py, do not edit\n")
        f.write("ITEM_MAPPING = {\n" + "".join(f"  [{i}] = {{\"{c}\", \"{t}\"}},\n" for i, (c, t) in sorted(item_map.items())) + "}\n")
        f.write("LOCATION_MAPPING = {\n" + "".join(f"  [{i}] = \"{p}\",\n" for i, p in sorted(loc_map.items())) + "}\n")
        f.write("CHAR_STORY = {\n" + "".join(f"  {c} = \"{s}\",\n" for c, s in sorted(story_of.items())) + "}\n")
        f.write("CHAR_CODE_BY_NAME = {\n" + "".join(f"  [\"{n}\"] = \"{code(n)}\",\n" for n in characters) + "}\n")
        f.write("WEAPON_CHAR = {\n" + "".join(
            f"  {k} = {{code = {('\"' + c + '\"') if c else 'nil'}, story = {('\"' + s + '\"') if s else 'nil'}, stage = {st}}},\n"
            for k, (c, s, st) in sorted(weapon_char.items())) + "}\n")
        f.write("STAGE_KEY = {" + ", ".join(f"{s} = \"{code(stage_unlock_name(s))}\"" for s in STORIES) + "}\n")
        f.write(f"KO_MILESTONES = {{{', '.join(map(str, KO_MILESTONES))}}}\n")
        f.write(f"STAGES_PER_STORY = {STAGES_PER_STORY}\n")
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump({"name": "Warriors Orochi Archipelago", "game_name": "Warriors Orochi", "package_version": VERSION,
                   "package_uid": "warriors_orochi_ap", "platform": "ps2", "author": "Justin",
                   "variants": {"standard": {"display_name": "Map Tracker", "flags": ["ap"]}}}, f, indent=1)
    print(f"pack written to {out}: {len(items)} items, {len(loc_map)} mapped locations")


if __name__ == "__main__":
    main(sys.argv[1])
