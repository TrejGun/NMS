# Aerial scan camera patch for No Man's Sky on Mac

This patch turns off the camera that flies upward and shows the area when you search for a place on a planet. On Mac, that camera change can hang the GPU. The Steam Mac build does not load the `MODS` folder, so the patch edits two of the game's own archives and saves the originals first.

Only data changes:

- `DoAerialScan` is turned off for planetary, star, and settlement charts
- the pause before that search drops from 6 seconds to 0.01
- if another scene still calls this camera, the pull-back distance is 0 and the move lasts 0.01 seconds
- the planet-discovery banner and the milestone popup become short

Creature and mineral scans keep their original timing.

## Requirements

- macOS and No Man's Sky from Steam
- Python 3.9 or newer, which macOS already includes
- the game fully quit

The first run creates a local `.venv`, installs `hgpaktool` there, and, when they are not already present, downloads the game-data compiler and .NET 8 into `tools/`. Those folders, temporary files, and backups stay out of the release.

## Install

1. Quit No Man's Sky so the process is no longer running.
2. In Finder, open the `mac` folder of this project.
3. Double-click `install.command`.
4. If macOS asks for permission to run it, allow it. The first time, you may need to right-click the file and choose Open.
5. Wait for `Installed. Restart No Man's Sky.` and press Return.
6. Start the game again.

The same step from Terminal:

```bash
cd /path/to/this/project
bash mac/bootstrap.sh
.venv/bin/python3 -m nmsfix install
```

If the Steam library is outside your home folder, point at it:

```bash
NMS_STEAM_ROOT="/Volumes/Games/Steam" .venv/bin/python3 -m nmsfix install
```

Or point at the archive folder itself:

```bash
NMS_BANKS="/path/to/No Man's Sky.app/Contents/Resources/GAMEDATA/MACOSBANKS" .venv/bin/python3 -m nmsfix install
```

The original `NMSARC.globals.pak` and `NMSARC.Precache.pak` are saved in `backups/vanilla`.

## Restore

1. Quit the game completely.
2. Double-click `mac/restore.command`.
3. Wait for `Restored the original archives.` and start the game again.

From Terminal:

```bash
.venv/bin/python3 -m nmsfix restore
```

Restore copies the archives from `backups/vanilla` back into the game. With that folder missing, there is nothing to restore.

## After a game update

A Steam update replaces the archives and removes the patch. Quit the game and run `mac/install.command` again. The installer sees the new originals, refreshes the backup, and applies the patch again.

Verifying file integrity in Steam does the same thing: it puts the original archives back. Run the installer again after that.

Running the installer again on an already patched game is safe. It keeps the first backup instead of replacing it with patched files.

## What goes into the release

The repository contains this guide, the Mac commands, and the code in `nmsfix/`.

These stay on your machine and stay out of the release:

- `.venv/` — the Python environment
- `tools/` — the compiler and .NET
- `work/` — temporary unpacked archives
- `backups/` — the original game archives
