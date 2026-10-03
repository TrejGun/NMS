import os
import subprocess

from nmsfix.errors import PatchError
from nmsfix.locations import DOTNET_ROOT, MBINCOMPILER


def to_mxml(mbin_path):
    _run(mbin_path)
    return mbin_path.with_suffix(".MXML")


def to_mbin(mxml_path):
    # MBINCompiler refuses to overwrite an existing file, and it writes the
    # extension in uppercase. On the default Mac filesystem that is the same
    # file as the lowercase source, so remove it first.
    mxml_path.with_suffix(".mbin").unlink(missing_ok=True)
    _run(mxml_path)
    compiled = mxml_path.with_suffix(".MBIN")
    if not compiled.is_file():
        raise PatchError(f"MBINCompiler did not write {compiled.name}")
    return compiled


def _run(path):
    if not MBINCOMPILER.is_file() or not (DOTNET_ROOT / "dotnet").is_file():
        raise PatchError("The local compiler is missing. Run mac/install.command once.")
    env = os.environ.copy()
    env["DOTNET_ROOT"] = str(DOTNET_ROOT)
    env["PATH"] = str(DOTNET_ROOT) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [str(MBINCOMPILER), str(path)],
        cwd=path.parent,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PatchError((result.stdout + result.stderr).strip())
