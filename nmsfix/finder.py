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
    dest_file = dest_dir / dest_name
    # "duplicate ... with replacing" into the Steam app returns a name clash.
    # Moving the live archive to the Trash first lets Finder write the new file.
    script = (
        'tell application "Finder"\n'
        f'  set destItem to POSIX file "{_applescript(dest_file)}" as alias\n'
        "  delete destItem\n"
        f'  duplicate POSIX file "{_applescript(staged)}" as alias to POSIX file "{_applescript(dest_dir)}" as alias\n'
        "end tell\n"
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"Finder could not install {dest_name}"
        raise PatchError(detail)


def _applescript(path):
    return str(path).replace("\\", "\\\\").replace('"', '\\"')
