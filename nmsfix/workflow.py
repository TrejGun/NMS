import hashlib
import shutil
import subprocess

from nmsfix import archives, compiler, finder
from nmsfix.errors import PatchError
from nmsfix.locations import BACKUP_DIR, INSTALLED_HASHES, WORK, game_banks
from nmsfix.patches import CHECKS, PATCHERS, TARGETS


def install():
    from nmsfix.toolchain import ensure_toolchain

    ensure_toolchain()
    _require_game_closed()
    banks = game_banks()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    installed_hashes = _read_hashes(INSTALLED_HASHES)
    patched = {}

    for pak_name, relative_files in TARGETS.items():
        source_pak = _require_pak(banks, pak_name)
        _backup_if_needed(source_pak, pak_name, installed_hashes)
        print(f"Unpacking {pak_name}")
        dest = WORK / pak_name
        original_names = archives.unpack(source_pak, dest)
        compiled = {
            relative: _patch_mbin(dest / relative, relative)
            for relative in relative_files
        }
        for relative, data in compiled.items():
            (dest / relative).write_bytes(data)

        output_pak = WORK / f"patched-{pak_name}"
        print(f"Repacking {pak_name}")
        archives.repack(dest / f"{pak_name}.manifest", output_pak)
        if archives.file_names(output_pak) != original_names:
            raise PatchError(f"{pak_name} file list changed during repack.")
        untouched = next(name for name in original_names if name not in relative_files)
        if archives.read_bytes(output_pak, untouched) != archives.read_bytes(source_pak, untouched):
            raise PatchError(f"Untouched file {untouched} changed inside {pak_name}.")
        _verify_pak(pak_name, output_pak, relative_files)
        patched[pak_name] = output_pak

    print("Installing into the game")
    for pak_name, output_pak in patched.items():
        finder.replace_in_folder(output_pak, banks, pak_name)
    for pak_name, relative_files in TARGETS.items():
        _verify_pak(pak_name, banks / pak_name, relative_files)
    _write_hashes(INSTALLED_HASHES, {name: _sha256(banks / name) for name in TARGETS})
    print("Installed. Restart No Man's Sky.")
    print(f"Original archives are in {BACKUP_DIR}")


def restore():
    _require_game_closed()
    banks = game_banks()
    missing = [name for name in TARGETS if not (BACKUP_DIR / name).is_file()]
    if missing:
        raise PatchError("No original backup was found. Nothing was restored.")
    for pak_name in TARGETS:
        print(f"Restoring {pak_name}")
        finder.replace_in_folder(BACKUP_DIR / pak_name, banks, pak_name)
    INSTALLED_HASHES.unlink(missing_ok=True)
    print("Restored the original archives. Restart No Man's Sky.")


def _patch_mbin(source_mbin, relative):
    if not source_mbin.is_file():
        raise PatchError(f"{relative} is not in the archive.")
    print(f"Patching {relative}")
    mxml = compiler.to_mxml(source_mbin)
    patched = PATCHERS[relative](mxml.read_text(encoding="utf-8"))
    mxml.write_text(patched, encoding="utf-8")
    compiled = compiler.to_mbin(mxml)
    data = compiled.read_bytes()
    mxml.unlink()
    return data


def _verify_pak(pak_name, pak_path, relative_files):
    for relative in relative_files:
        check = CHECKS.get(relative)
        if check is None:
            continue
        extracted = WORK / f"verify-{relative.replace('/', '-')}"
        extracted.write_bytes(archives.read_bytes(pak_path, relative))
        mxml = compiler.to_mxml(extracted)
        check(mxml.read_text(encoding="utf-8"))
        mxml.unlink()
    print(f"Verified {pak_name}")


def _backup_if_needed(source_pak, pak_name, installed_hashes):
    backup = BACKUP_DIR / pak_name
    live_hash = _sha256(source_pak)
    if not backup.exists():
        print(f"Backing up {pak_name}")
        shutil.copy2(source_pak, backup)
    elif live_hash != _sha256(backup) and live_hash != installed_hashes.get(pak_name):
        print(f"Game update detected, refreshing the backup of {pak_name}")
        shutil.copy2(source_pak, backup)


def _require_pak(banks, pak_name):
    source_pak = banks / pak_name
    if not source_pak.is_file():
        raise PatchError(f"Missing {source_pak}")
    return source_pak


def _require_game_closed():
    result = subprocess.run(
        ["pgrep", "-f", "No Man's Sky.app/Contents/MacOS/No Man's Sky"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        raise PatchError("Quit No Man's Sky completely, then run this again.")


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_hashes(path):
    hashes = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            hashes[name] = digest
    return hashes


def _write_hashes(path, hashes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in hashes.items()),
        encoding="utf-8",
    )
