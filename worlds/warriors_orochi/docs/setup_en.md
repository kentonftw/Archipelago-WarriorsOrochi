# Warriors Orochi (PS2) – Archipelago Setup

## What you need
- Archipelago 0.6.7 or newer
- PCSX2 2.x with your own PS2 BIOS
- Warriors Orochi, **NTSC-U (SLUS-21662)**. Other regions use different memory addresses and will not work.

## Install
1. Put `warriors_orochi.apworld` in Archipelago's `custom_worlds` folder (or double-click it).
2. Generate a seed with a YAML like:
   ```yaml
   name: YourName
   game: Warriors Orochi
   Warriors Orochi:
     gaiden_stage_checks: true
     last_gaiden_checks: false
     gaiden_unlock_checks: false
     story_character_requirement: 4
   ```

## PCSX2
1. Tools → **Show Advanced Settings**.
2. Settings → Advanced → **PINE Settings**: tick **Enable**, Slot **28011**.
3. Start Warriors Orochi.

## Play
1. Open **Warriors Orochi Client** from the Archipelago Launcher and connect to your room.
2. The client shows "Connected to PCSX2" once the game is running.
3. Clear story stages and Gaiden stages to send checks. Characters you receive appear in Change Character.

Client commands: `/pcsx2` (connection status), `/roster` (characters the game currently has).

## How characters work
In Story Mode you can only field characters recruited by that story (e.g. Okuni belongs to the
Samurai story). Received characters always appear in Free Mode, and in Story Mode only in their home story.

## Known limitations (v0.8)
- Logic is "soft": the game does not stop you playing later stages early.
- With Gaiden unlock checks on, a Gaiden objective is only detected if you have not already
  received that character.
- Death Link and traps do nothing while an Infinite Health or Infinite Musou cheat is active.
- With Stage Locks on, keep the client connected while you play: it is what hides locked stages.
  If you save while a stage is hidden, it reappears the next time the client sees you have its item.
- Do not swap a character out of your active team while the client is removing them.
