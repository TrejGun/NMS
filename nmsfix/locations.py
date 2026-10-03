import os
import re
from pathlib import Path

from nmsfix.errors import PatchError

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
WORK = ROOT / "work"
BACKUP_DIR = ROOT / "backups" / "vanilla"
INSTALLED_HASHES = ROOT / "backups" / "installed.sha256"
MBINCOMPILER = TOOLS / "MBINCompiler-macOS" / "MBINCompiler"
DOTNET_ROOT = TOOLS / "dotnet"

BANKS_TAIL = Path(
    "steamapps/common/No Man's Sky/No Man's Sky.app/Contents/Resources/GAMEDATA/MACOSBANKS"
)


def steam_libraries():
    libraries = []
    default = Path.home() / "Library/Application Support/Steam"
    vdf = default / "steamapps/libraryfolders.vdf"
    if vdf.is_file():
        for match in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(errors="replace")):
            libraries.append(Path(match))
    if default not in libraries:
        libraries.insert(0, default)
    override = os.environ.get("NMS_STEAM_ROOT")
    if override:
        libraries.insert(0, Path(override))
    return libraries


def game_banks():
    override = os.environ.get("NMS_BANKS")
    if override:
        banks = Path(override)
        if not banks.is_dir():
            raise PatchError(f"NMS_BANKS does not point at a folder: {banks}")
        return banks
    for library in steam_libraries():
        banks = library / BANKS_TAIL
        if banks.is_dir():
            return banks
    raise PatchError(
        "No Man's Sky archives were not found. Install the Steam Mac version, "
        "or set NMS_BANKS to the MACOSBANKS folder."
    )
