"""Pinned 7 Days to Die game version.

All generated mods target this version. When a new major game release changes
XML schemas, update GAME_VERSION and GAME_BUILD and rebuild the app.
"""
from __future__ import annotations

GAME_VERSION = "2.5"
GAME_BUILD = "b32"
GAME_VERSION_LABEL = f"v{GAME_VERSION} ({GAME_BUILD})"

# ---------------------------------------------------------------------------
# Shim TypedDict / helpers — kept so existing routes (item, block, recipe,
# perk) and tests that import VersionDef / get_version continue to work.
# ---------------------------------------------------------------------------

from typing import TypedDict


class VersionDef(TypedDict):
    id: str
    label: str
    notes: str
    details: list[str]


_PINNED: VersionDef = {
    "id": "v2_5",
    "label": GAME_VERSION_LABEL,
    "notes": (
        f"Generated for 7 Days to Die {GAME_VERSION_LABEL}. "
        "If the game has updated since this mod was created, verify property "
        "names against vanilla XML files before using."
    ),
    "details": [
        f"Target: 7 Days to Die {GAME_VERSION_LABEL}",
        "XPath modding via Config/*.xml files",
        "Install by copying the mod folder into your Mods directory",
        "Check the in-game console (F1) for XML errors if the mod fails to load",
    ],
}

SUPPORTED_VERSIONS: list[VersionDef] = [_PINNED]
VERSION_MAP: dict[str, VersionDef] = {_PINNED["id"]: _PINNED}
DEFAULT_VERSION_ID = _PINNED["id"]


def get_version(version_id: str = DEFAULT_VERSION_ID) -> VersionDef:
    """Return the pinned VersionDef. version_id is accepted but ignored."""
    return _PINNED
