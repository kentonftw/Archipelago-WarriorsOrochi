# Warriors Orochi (PS2, NTSC-U SLUS-21662) – Archipelago research notes

All addresses are PS2 EE-RAM addresses (use these with PINE / pnach). In Cheat Engine,
add them to the EE base (find it with `eebase()` in the Lua Engine).

## Confirmed
| Address | Type | What | How we know |
|---|---|---|---|
| `0x004C9150` | 79 x 0xC8-byte records | Character records, roster order. +0x04 level-1, +0x08 five u16 stats (Life/Musou/Atk/Def/Spd), +0x14 u16 EXP | Levelled Xing Cai 1->2, only her record changed |
| `0x004CCF0C` | 10 bytes (79 bits) | **Character unlocked** bitfield, bit N = roster index N | Yue Ying (41) + Magoichi (57) bits appeared after Shu Stage 2; matches cheat-site unlock list; 12 starting characters = 12 bits on a fresh save |
| `0x004CCF18` / `1C` / `20` / `24` | u32 each | **Story progress** (stages cleared) for Shu / Wei / Wu / Samurai | Shu 1->2 after Stage 2; Wei, Wu, Samurai 0->1 after Stage 1 (watch log), written with the unlock bits |
| `0x004CD210` | u32 | Growth points | Matches on-screen value (6020, 12637, 11505) |
| `0x004CD52C` | u32 | KO count (resets at camp) | Edited to 500, HUD showed 500 |
| `0x004CCF28` | 61 x 12-byte records | **Per-stage records**: u32 best time (frames; 0x34BC0 = none), u32 best KOs, u32 status (0 locked, 1/2 available, **3 cleared**) | Shu Gaiden 2 went 1->3 on clear; Wei 1 / Wu 1 / Samurai 1 went 2->3 |
| `0x0031FBCA` | 61 x 6-byte entries | **Per-stage recruit table**: bytes 1-3 = characters recruited by clearing the stage (0x4F = none). Story Mode only lets you field characters recruited by that story's stages | Entries match cheat-site unlocks (Shu 2 = Yue Ying + Magoichi, Samurai 1 = Huang Zhong + Guan Ping); confirmed in-game that Okuni shows only in the Samurai story |
| `0x00321048` | strings | Character name table (roster order) | Read from dump |

Important behaviour: on the "New Character" screen the unlock bits are **not** set yet.
The game commits the bits, the story counter and other progress when you return to camp.

## Battle units (CONFIRMED 2026-11-22)
| Address | What |
|---|---|
| `0x004DD5C0 + k*0xD0` | Unit list, k = 0 is the player. Each unit: u16 max HP at +0, u16 current HP at +2 |
| unit - 0x0C | `FF FF FF FF` marker on every live unit |
| unit - 0x04 | Side/army byte. Player's army = 3; Orochi army = 2 in both tested battles; other numbers (0, 1) are other armies in the stage |
Zhang Jiao (135 HP) was unit k=116 in Samurai Stage 1-era battle. ~128 slots.
One-hit-kill testing cheat: `WarriorsOrochi_testing.CT` (Cheat Engine table) keeps side-2 units at 1 HP.
Set `WO_ENEMY_SIDE = 1` (Lua Engine) before ticking it if a stage's enemies use another side number.

## From decrypted CodeBreaker codes (not yet re-verified)
| Address | What |
|---|---|
| `0x004DD5C0` / `0x004DD5C2` | Player 1 max / current HP (u16) |
| `0x004DD5C6` / `0x004DD5C8` | Player 1 max / current Musou (u16) |
| `0x004CD598` | Player 1 power-up flags (byte), timers u32 at `0x004CD5A0..AC` |
| `0x004CD22F`, `0x004CD230` | Movie unlock bits |
| `0x001F19FC` | Mission timer code patch |

## Probable / to test next
| Address | Guess | Next test |
|---|---|---|
| `0x004CD236` | Current/last stage ID (0x0C during Shu Stage 2) | Start Wei Stage 1, watch it change |
| `0x004CD214` (26 bytes, values 12/14/00) | Unknown. NOT character unlocks and NOT stage availability (both tested: zeroing it changed nothing) | - |
| `0x004CCF90`-`0x004CD1A0` | Per-stage records (best time/KOs?) written on first clear of each stage | Could detect Gaiden clears |
| `0x004CD008`, `0x004CD17C` | Changed 0->1 and 1->3 after Shu Stage 2 | Watcher |

## Roster index (bit) order
0 Zhao Yun, 1 Guan Yu, 2 Zhang Fei, 3 Xiahou Dun, 4 Dian Wei, 5 Xu Zhu, 6 Zhou Yu, 7 Lu Xun,
8 Taishi Ci, 9 Diao Chan, 10 Zhuge Liang, 11 Cao Cao, 12 Lu Bu, 13 Sun Shang Xiang, 14 Liu Bei,
15 Sun Jian, 16 Sun Quan, 17 Dong Zhuo, 18 Yuan Shao, 19 Ma Chao, 20 Huang Zhong, 21 Xiahou Yuan,
22 Zhang Liao, 23 Sima Yi, 24 Lu Meng, 25 Gan Ning, 26 Jiang Wei, 27 Zhang Jiao, 28 Xu Huang,
29 Zhang He, 30 Zhen Ji, 31 Huang Gai, 32 Sun Ce, 33 Wei Yan, 34 Pang Tong, 35 Meng Huo,
36 Zhu Rong, 37 Da Qiao, 38 Xiao Qiao, 39 Cao Ren, 40 Zhou Tai, 41 Yue Ying, 42 Cao Pi,
43 Pang De, 44 Ling Tong, 45 Guan Ping, 46 Xing Cai, 47 Zuo Ci, 48 Sanada Yukimura,
49 Maeda Keiji, 50 Oda Nobunaga, 51 Akechi Mitsuhide, 52 Ishikawa Goemon, 53 Uesugi Kenshin,
54 Oichi, 55 Okuni, 56 Kunoichi, 57 Saika Magoichi, 58 Takeda Shingen, 59 Date Masamune,
60 Lady Noh, 61 Hattori Hanzo, 62 Mori Ranmaru, 63 Toyotomi Hideyoshi, 64 Imagawa Yoshimoto,
65 Honda Tadakatsu, 66 Inahime, 67 Tokugawa Ieyasu, 68 Ishida Mitsunari, 69 Azai Nagamasa,
70 Shima Sakon, 71 Shimazu Yoshihiro, 72 Tachibana Ginchiyo, 73 Naoe Kanetsugu, 74 Nene,
75 Fuma Kotaro, 76 Miyamoto Musashi, 77 Orochi, 78 Da Ji

## Tools in this folder
- `warriors_orochi.apworld` – the Archipelago world + client (v0.1).
- `worlds/warriors_orochi/` – same thing as source.
- `tools/wo_probe.py` – checks the PINE connection; `watch` mode logs save-data changes while you play.
- `tools/cbdecrypt.py` – CodeBreaker V1/V7 code decryptor.
- `SLUS-21662_2030F647.pnach` – raw testing cheats (copy into Documents\PCSX2\cheats).
- `*.bin` – 32 MB RAM dumps taken during testing.

## Cheat Engine Lua helpers (paste into Table -> Show Cheat Table Lua Script if CE was restarted)
```lua
DUMPDIR = [[C:\path\to\your\folder\]]
function eebase() local r=AOBScan('0D 00 40 14 2D 20 00 02 F6 81 04 0C 00 00 00 00 2D 20 00 02 2D 88 40 00','') local a=tonumber(r[0],16)-0x120000 r.destroy() return a end
function wodump(name) local b=eebase() print(name..' -> '..tostring(writeRegionToFile(DUMPDIR..name..'.bin', b, 0x2000000))) end
```

## Stage record index (record N <-> recruit entry N) - ALL 60 MAPPED
Method: recruit-table bytes 4/5 are each stage's "personal item" characters; matched to the
community personal-item lists (koei fandom Story Mode page, GameFAQs PI guides). 6 confirmed in-game.
Story:  Shu 1=35 2=49 3=18 4=24 5=10 6=7 7=36 8=58 | Wei 1=47 2=25 3=13 4=23 5=40 6=27 7=54 8=56
        Wu 1=21 2=14 3=38 4=37 5=46 6=19 7=44 8=57 | Samurai 1=9 2=52 3=43 4=17 5=12 6=22 7=30 8=59
Gaiden: Shu 2=4 3=45 4=16 5=26 6=55 7=0 8=53 | Wei 2=20 3=5 4=51 5=32 6=2 7=1 8=28
        Wu 2=8 3=33 4=31 5=34 6=50 7=3 8=15 | Samurai 2=42 3=11 4=6 5=48 6=39 7=41 8=29
Record 60 is not a stage. Status byte = 0x004CCF28 + record*12 + 8 (3 = cleared).
Stage availability follows the story progress counter (clearing chapter N opens chapter N+1 and Gaiden N+1);
Gaiden 8 additionally needs a special Chapter 7 objective.

## Tests
`worlds/warriors_orochi/test/` - run from an Archipelago source checkout with
`python -m pytest worlds/warriors_orochi/test`.

## Player battle unit (confirmed 2026-11-22)
0x4DD5B4 = FFFFFFFF in battle. 0x4DD5C0 max HP, C2 cur HP, C4 ?, C6 max Musou, C8 cur Musou,
CA Attack (writing it changes real damage; reset on character switch), CC Defense?, CE ?.
Writing cur HP (C2) = 0 soft-locks the character. Setting it to 1 and taking a hit gives a normal defeat.
On the defeat screen C2 = 0 and the 0x4DD5B4 marker is still FFFFFFFF. C4 trails C2 (display HP).

## Weapons (confirmed 2026-11-22, Hideyoshi weapon pickup)
Character record +0x18: 7 weapon slots x 0x16 bytes. Slot u16 = weapon id, 0x159 = empty.
Weapon id = roster index * 4 + level - 1 (Hideyoshi #63 Lv1 = 252; Ieyasu 268, Shimazu 284).
Written to the record only when returning to camp. In-battle pickup buffer around 0x4CD264.
Record +0x00 u32 ? (Zhao Yun 3000), +0x12 u16 = 8000 for all?  Personal item flag: not found yet.

## Stage locks (confirmed 2026-11-22, Free Mode AND Story Mode)
Stage record status byte: 0 = locked/hidden, 2 = open, 3 = cleared. Writing it directly changes Select Scenario.

## Abilities (confirmed 2026-11-22) - shared by the whole army
0x4CD214: 7 "in use" slots, ability id each, 18 = empty (equipping Speed wrote 8).
0x4CD21B: 18 bytes of levels, value = level-1, 20 = not acquired. Index = screen grid column by column:
0 Vitality 1 Focus 2 Potence 3 Fortitude 4 Impulse 5 Cavalier | 6 Karma 7 Power 8 Speed 9 Technique
10 Boost 11 Awakening | 12 Acclaim 13 Recuperate 14 Conserve 15 Adrenalin 16 Recover 17 Refill
Character record +0x12 u16 grows with use (Hideyoshi 8000, Akechi 1098): maybe ability/proficiency points.

## Publishing
GitHub: https://github.com/kentonftw/Archipelago-WarriorsOrochi (public, MIT).
To release: bump world_version in worlds/warriors_orochi/archipelago.json and push to main; the
Release workflow runs the tests, builds the .apworld and PopTracker zip, and publishes vX.Y.Z.

## In-game notices (confirmed 2026-11-22, Shu Stage 1)
Pop-up text pointer table at 0x331F18 (entries: new ability 0x32E6D0, unique item 0x32E700, new weapon 0x32E760,
"%s has become available for use." 0x32E780, "A new scenario has become available." 0x32E7B0).
Overwriting 0x32E780 during battle changed the NEW CHARACTER screen text; "[01word]" renders red.
0x4CD4F4 (and 0x4CD4F8) = stage record of the battle being played (35 = Shu 1, 47 = Wei 1).
Battle message templates (stage data, ~0x1F4E3C0): "[03%s] has been defeated!" etc.
