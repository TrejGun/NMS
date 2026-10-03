import shutil
from pathlib import Path

from nmsfix.errors import PatchError


def _api():
    from hgpaktool.api import HGPAKFile
    from hgpaktool.constants import Platform

    return HGPAKFile, Platform.MAC


def file_names(pak_path):
    HGPAKFile, platform = _api()
    with HGPAKFile(pak_path, platform) as pak:
        return list(pak.filenames)


def unpack(pak_path, dest):
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    HGPAKFile, platform = _api()
    with HGPAKFile(pak_path, platform) as pak:
        count = pak.unpack(dest, write_manifest=True)
        names = list(pak.filenames)
    if count != len(names):
        raise PatchError(f"Unpacked {count} files from {pak_path.name}, index has {len(names)}.")
    return names


def repack(manifest, output_pak):
    HGPAKFile, platform = _api()
    HGPAKFile.repack(manifest, output_pak, compress=True, platform=platform)


def read_bytes(pak_path, internal_name):
    HGPAKFile, platform = _api()
    with HGPAKFile(pak_path, platform) as pak:
        return b"".join(pak._extract_file_compressed(internal_name))
