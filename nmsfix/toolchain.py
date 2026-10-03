import stat
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from nmsfix.errors import PatchError
from nmsfix.locations import DOTNET_ROOT, MBINCOMPILER, TOOLS

MBINCOMPILER_URL = (
    "https://github.com/monkeyman192/MBINCompiler/releases/download/"
    "v7.04.1-pre3/MBINCompiler-macOS.zip"
)
DOTNET_INSTALL_URL = "https://dot.net/v1/dotnet-install.sh"


def ensure_toolchain():
    TOOLS.mkdir(parents=True, exist_ok=True)
    if not (DOTNET_ROOT / "dotnet").is_file():
        _install_dotnet()
    if not MBINCOMPILER.is_file():
        _install_mbincompiler()
    _hide_quarantine(MBINCOMPILER)


def _install_dotnet():
    print("Downloading the .NET 8 runtime")
    script = TOOLS / "dotnet-install.sh"
    _download(DOTNET_INSTALL_URL, script)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    result = subprocess.run(
        ["bash", str(script), "--runtime", "dotnet", "--channel", "8.0", "--install-dir", str(DOTNET_ROOT)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not (DOTNET_ROOT / "dotnet").is_file():
        raise PatchError((result.stdout + result.stderr).strip() or "The .NET runtime did not install.")


def _install_mbincompiler():
    print("Downloading MBINCompiler")
    archive = TOOLS / "MBINCompiler-macOS.zip"
    _download(MBINCOMPILER_URL, archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(TOOLS)
    if not MBINCOMPILER.is_file():
        raise PatchError("MBINCompiler was not inside the downloaded archive.")
    MBINCOMPILER.chmod(MBINCOMPILER.stat().st_mode | stat.S_IEXEC)


def _download(url, dest):
    try:
        urllib.request.urlretrieve(url, dest)
    except OSError as error:
        raise PatchError(f"Could not download {url}: {error}") from error


def _hide_quarantine(path):
    subprocess.run(
        ["xattr", "-dr", "com.apple.quarantine", str(Path(path).parent)],
        capture_output=True,
        text=True,
    )
