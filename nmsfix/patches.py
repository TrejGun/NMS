import re

from nmsfix.errors import PatchError

AERIAL_VALUE = re.compile(
    r'<Property name="(Time|TimeBack|StartTime|PauseTime|LookTime|Distance)" value="[^"]*" />'
)
SCAN_DELAY = re.compile(
    r'(<Property name="DoAerialScan" value=")true(" />\s*'
    r'<Property name="UseMissionIDSeedForEvent" value="(?:true|false)" />\s*'
    r'<Property name="StartDelay" value=")6\.000000(" />)',
    re.MULTILINE,
)
PROPERTY_VALUE = re.compile(
    r'(<Property name="{name}" value=")[^"]*(" />)'
)

UI_TIMES = {
    "MilestoneStingDisplayTime": "0.050000",
    "StageStingDisplayTime": "0.050000",
    "DiscoverPlanetTotalTime": "0.200000",
    "DiscoverPlanetMessageWait": "0.050000",
    "DiscoverPlanetMessageTime": "0.200000",
}

# pak name -> internal files this patch rewrites
TARGETS = {
    "NMSARC.globals.pak": [
        "gccameraglobals.global.mbin",
        "gcuiglobals.global.mbin",
    ],
    "NMSARC.Precache.pak": [
        "metadata/reality/tables/rewardtable.mbin",
    ],
}

PATCHERS = {}


def set_property(text, name, value):
    pattern = re.compile(PROPERTY_VALUE.pattern.format(name=re.escape(name)))
    updated, count = pattern.subn(rf"\g<1>{value}\2", text, count=1)
    if count != 1:
        raise PatchError(f"Expected one {name} property, found {count}.")
    return updated


def patch_camera(text):
    start = text.find('<Property name="AerialViewDataTable">')
    end = text.find('<Property name="SClassLandingShakeMultiplier"', start)
    if start < 0 or end < 0:
        raise PatchError("AerialViewDataTable was not found in the camera globals.")

    def replace(match):
        name = match.group(1)
        value = "0.000000" if name == "Distance" else "0.010000"
        return f'<Property name="{name}" value="{value}" />'

    return text[:start] + AERIAL_VALUE.sub(replace, text[start:end]) + text[end:]


def patch_ui(text):
    for name, value in UI_TIMES.items():
        text = set_property(text, name, value)
    return text


def patch_reward(text):
    text, delay_count = SCAN_DELAY.subn(r"\1false\g<2>0.010000\3", text)
    text, flag_count = re.subn(
        r'<Property name="DoAerialScan" value="true" />',
        '<Property name="DoAerialScan" value="false" />',
        text,
    )
    if delay_count < 70 or (delay_count + flag_count) < 76:
        raise PatchError(
            "The reward table has fewer aerial scans than this patch expects. "
            f"Found {delay_count} delayed scans and {flag_count} other scans. "
            "The game data may have changed."
        )
    check_reward(text)
    return text


def check_reward(text):
    if 'DoAerialScan" value="true"' in text:
        raise PatchError("Aerial scan is still enabled in the reward table.")


def check_camera(text):
    start = text.find('<Property name="AerialViewDataTable">')
    end = text.find('<Property name="SClassLandingShakeMultiplier"', start)
    section = text[start:end]
    if 'name="Distance" value="0.000000"' not in section:
        raise PatchError("Aerial camera distance was not zeroed.")
    if re.search(r'name="Distance" value="(?!0\.000000")[^"]+"', section):
        raise PatchError("An aerial camera distance is still non-zero.")


PATCHERS["gccameraglobals.global.mbin"] = patch_camera
PATCHERS["gcuiglobals.global.mbin"] = patch_ui
PATCHERS["metadata/reality/tables/rewardtable.mbin"] = patch_reward

CHECKS = {
    "gccameraglobals.global.mbin": check_camera,
    "metadata/reality/tables/rewardtable.mbin": check_reward,
}
