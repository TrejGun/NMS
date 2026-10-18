import re

from nmsfix.errors import PatchError

SCAN_DELAY = re.compile(
    r'(<Property name="DoAerialScan" value=")true(" />\s*'
    r'<Property name="UseMissionIDSeedForEvent" value="(?:true|false)" />\s*'
    r'<Property name="StartDelay" value=")6\.000000(" />)',
    re.MULTILINE,
)
BRAIN_AERIAL = re.compile(
    r'(<Property name="Event" value="SE_SHIPBRAIN_CLEANSE" />\s*'
    r'<Property name="Time" value="[^"]*" />\s*'
    r'<Property name="DoAerialScan" value=")true(" />)'
)
BRAIN_DONE = re.compile(
    r'<Property name="Event" value="SE_SHIPBRAIN_CLEANSE" />\s*'
    r'<Property name="Time" value="[^"]*" />\s*'
    r'<Property name="DoAerialScan" value="false" />'
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

# Reward ids that must not start the fly-up. The patch still turns the flag
# off for every other reward. R_CHART_ROBOT is the echo locator.
REQUIRED_REWARDS = (
    "R_CHART_ROBOT",
)

# pak name -> internal files this patch rewrites
# The aerial camera itself stays at the game's original length. Cutting that
# move to 0.01s returns control before the player model and weapons reload.
# Charts skip the move entirely through DoAerialScan below.
TARGETS = {
    "NMSARC.globals.pak": [
        "gcuiglobals.global.mbin",
    ],
    "NMSARC.Precache.pak": [
        "metadata/reality/tables/rewardtable.mbin",
        "metadata/simulation/missions/tables/startedonusemissiontable.mbin",
    ],
}

PATCHERS = {}


def set_property(text, name, value):
    pattern = re.compile(PROPERTY_VALUE.pattern.format(name=re.escape(name)))
    updated, count = pattern.subn(rf"\g<1>{value}\2", text, count=1)
    if count != 1:
        raise PatchError(f"Expected one {name} property, found {count}.")
    return updated


def patch_ui(text):
    for name, value in UI_TIMES.items():
        text = set_property(text, name, value)
    return text


def patch_reward(text):
    if 'DoAerialScan" value="true"' not in text:
        return text
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


def reward_section(text, reward_id):
    marker = f'_id="{reward_id}">'
    start = text.find(marker)
    if start < 0:
        raise PatchError(f"Reward {reward_id} was not found in the reward table.")
    nxt = text.find('_id="', start + len(marker))
    return text[start:] if nxt < 0 else text[start:nxt]


def check_reward(text):
    if 'DoAerialScan" value="true"' in text:
        raise PatchError("Aerial scan is still enabled in the reward table.")
    for reward_id in REQUIRED_REWARDS:
        section = reward_section(text, reward_id)
        if 'DoAerialScan" value="false"' not in section:
            raise PatchError(f"{reward_id} does not disable the aerial camera.")


def patch_brain(text):
    updated, count = BRAIN_AERIAL.subn(r"\1false\2", text, count=1)
    if count == 0 and not BRAIN_DONE.search(text):
        raise PatchError("The Hyaline Brain scan was not found in the mission table.")
    check_brain(updated)
    return updated


def check_brain(text):
    if not BRAIN_DONE.search(text):
        raise PatchError("The Hyaline Brain scan still starts the aerial camera.")
    if BRAIN_AERIAL.search(text):
        raise PatchError("The Hyaline Brain scan still starts the aerial camera.")


PATCHERS["gcuiglobals.global.mbin"] = patch_ui
PATCHERS["metadata/reality/tables/rewardtable.mbin"] = patch_reward
PATCHERS["metadata/simulation/missions/tables/startedonusemissiontable.mbin"] = patch_brain

CHECKS = {
    "metadata/reality/tables/rewardtable.mbin": check_reward,
    "metadata/simulation/missions/tables/startedonusemissiontable.mbin": check_brain,
}
