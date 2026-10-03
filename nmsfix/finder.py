import shutil
import subprocess

from nmsfix.errors import PatchError
from nmsfix.locations import WORK


def replace_in_folder(src, dest_dir, dest_name):
    """Copy src into a Mac app bundle under dest_name.

    This process cannot create files inside the Steam app. Finder can replace
    an archive when the file it copies already has the destination name.
    """
    staging = WORK / "install-staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    staged = staging / dest_name
    shutil.copy2(src, staged)
    script = (
        'tell application "Finder"\n'
        f'  duplicate POSIX file "{_applescript(staged)}" to POSIX file "{_applescript(dest_dir)}" with replacing\n'
        "end tell\n"
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"Finder could not install {dest_name}"
        raise PatchError(detail)


def _applescript(path):
    return str(path).replace("\\", "\\\\").replace('"', '\\"')
