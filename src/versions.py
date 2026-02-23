"""Supported 7 Days to Die game versions and per-version compatibility notes.

These are used both in the UI and snapshotted into every generated mod's README.
"""
from __future__ import annotations

from typing import TypedDict


class VersionDef(TypedDict):
    id: str
    label: str
    notes: str
    # Key structural differences relevant to XML modding
    details: list[str]


SUPPORTED_VERSIONS: list[VersionDef] = [
    {
        "id": "v1",
        "label": "V1.0+ (1.x Stable)",
        "notes": (
            "Recommended target. V1.0 introduced significant XML restructuring. "
            "Biome-specific loot is split into separate loot_<biome>.xml files. "
            "Progression uses the updated format with skill point costs per rank."
        ),
        "details": [
            "Biome loot split: loot_<biome>.xml instead of a single loot.xml",
            "progression.xml uses <progression> root with updated rank/cost schema",
            "blocks.xml supports new 'UpgradeBlockValue' path for tier blocks",
            "Solar bank output set via blocks.xml property 'PowerOutput'",
            "Recipe 'craftingTime' attribute replaces older timing approach",
        ],
    },
    {
        "id": "a21",
        "label": "Alpha 21 (Stable)",
        "notes": (
            "A21 introduced XPath-based modding. Most mod structures work as-is "
            "but loot.xml is a single file and progression.xml has an older schema. "
            "Some block and item property names differ from V1.x."
        ),
        "details": [
            "Single loot.xml — no biome split",
            "progression.xml uses older <perk> structure inside <perks>",
            "Solar bank output set via the 'electricbase' property in blocks.xml",
            "Recipe 'count' attribute used for ingredient amounts",
            "Item property names may differ — check vanilla files for reference",
        ],
    },
    {
        "id": "exp",
        "label": "Experimental (Latest)",
        "notes": (
            "Generates V1.x-compatible XML but targets the current experimental branch. "
            "Schema details may have changed since this tool was last updated. "
            "Test in-game carefully and compare against current vanilla XML files."
        ),
        "details": [
            "Based on V1.x structure — experimental branches may introduce new schemas",
            "Always verify against the current vanilla XML files in your install",
            "Log errors in the in-game console (F1) if the mod fails to load",
        ],
    },
]

# Lookup: version id → VersionDef
VERSION_MAP: dict[str, VersionDef] = {v["id"]: v for v in SUPPORTED_VERSIONS}

DEFAULT_VERSION_ID = "v1"


def get_version(version_id: str) -> VersionDef:
    """Return the VersionDef for the given id, falling back to the default."""
    return VERSION_MAP.get(version_id, VERSION_MAP[DEFAULT_VERSION_ID])
