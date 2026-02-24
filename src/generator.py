"""XML generator for 7 Days to Die modlets.

All XML is produced with stdlib xml.etree.ElementTree + xml.dom.minidom.
No external dependencies required.

Each public generate_* function accepts a dict of form values and returns a
dict mapping relative file paths (inside the ZIP folder) to string content.

PRESETS provides starter defaults for each mod type, keyed by type then name.
"""
from __future__ import annotations

import io
import zipfile
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import Any

from .versions import GAME_VERSION_LABEL, VersionDef, get_version

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pretty(root: ET.Element) -> str:
    """Return a pretty-printed UTF-8 XML string from an ElementTree element."""
    raw = ET.tostring(root, encoding="unicode")
    dom = xml.dom.minidom.parseString(raw)
    pretty = dom.toprettyxml(indent="  ")
    # Replace the auto-generated declaration with a clean UTF-8 one.
    lines = pretty.splitlines()
    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines) + "\n"


def _configs_root() -> ET.Element:
    """Return a <configs> root element for XPath-based mod files."""
    return ET.Element("configs")


def _append_el(parent: ET.Element, xpath: str) -> ET.Element:
    """Add <append xpath="..."> to a configs root."""
    el = ET.SubElement(parent, "append")
    el.set("xpath", xpath)
    return el


def _set_el(parent: ET.Element, xpath: str, value: str) -> ET.Element:
    """Add <set xpath="...">value</set> to a configs root."""
    el = ET.SubElement(parent, "set")
    el.set("xpath", xpath)
    el.text = value
    return el


def _prop(parent: ET.Element, name: str, value: str) -> ET.Element:
    el = ET.SubElement(parent, "property")
    el.set("name", name)
    el.set("value", value)
    return el


def _prop_class(parent: ET.Element, name: str) -> ET.Element:
    el = ET.SubElement(parent, "property")
    el.set("class", name)
    return el


def _prop_param(parent: ET.Element, name: str, param1: str) -> ET.Element:
    el = ET.SubElement(parent, "property")
    el.set("name", name)
    el.set("param1", param1)
    return el


def _comment(parent: ET.Element, text: str) -> None:
    """Append an XML comment node."""
    parent.append(ET.Comment(text))


# ---------------------------------------------------------------------------
# ModInfo.xml
# ---------------------------------------------------------------------------


def make_modinfo_xml(
    name: str,
    display_name: str = "",
    description: str = "",
    author: str = "",
    version: str = "1.0",
    website: str = "",
) -> str:
    root = ET.Element("xml")
    info = ET.SubElement(root, "ModInfo")
    ET.SubElement(info, "Name").set("value", name)
    ET.SubElement(info, "DisplayName").set("value", display_name or name)
    ET.SubElement(info, "Version").set("value", version)
    ET.SubElement(info, "Description").set("value", description)
    ET.SubElement(info, "Author").set("value", author)
    if website:
        ET.SubElement(info, "Website").set("value", website)
    return _pretty(root)


# ---------------------------------------------------------------------------
# README.txt
# ---------------------------------------------------------------------------


def make_readme_txt(
    mod_name: str,
    mod_type: str,
    form_data: dict[str, Any],
    version_def: VersionDef,
) -> str:
    lines: list[str] = [
        "=" * 60,
        f"  {mod_name}",
        "=" * 60,
        "",
        f"Mod type    : {mod_type.replace('_', ' ').title()}",
        f"Target game : {version_def['label']}",
        "",
        "DESCRIPTION",
        "-" * 40,
        form_data.get("description") or "(No description provided.)",
        "",
        "VERSION NOTES",
        "-" * 40,
        version_def["notes"],
        "",
        "VERSION DETAILS",
        "-" * 40,
    ]
    for detail in version_def["details"]:
        lines.append(f"  - {detail}")
    lines += [
        "",
        "INSTALLATION",
        "-" * 40,
        "1. Locate your 7 Days to Die installation Mods folder:",
        "     Windows : %APPDATA%\\7DaysToDie\\Mods\\",
        "             or  <Steam>\\steamapps\\common\\7 Days to Die\\Mods\\",
        "     Linux   : ~/.local/share/7DaysToDie/Mods/",
        "             or  <Steam>/steamapps/common/7 Days to Die/Mods/",
        "     macOS   : ~/Library/Application Support/7DaysToDie/Mods/",
        "   (Create the Mods folder if it does not exist.)",
        "",
        f"2. Copy the '{mod_name}' folder from this ZIP into your Mods folder.",
        "",
        f"3. Verify the structure looks like:",
        f"     Mods/",
        f"       {mod_name}/",
        f"         ModInfo.xml",
        f"         Config/",
        f"           *.xml",
        "",
        "4. Launch 7 Days to Die. The mod will be loaded automatically.",
        "",
        "5. Check the in-game console (F1) for any XML errors if the mod",
        "   does not appear to work. Common issues:",
        "     - Wrong folder depth (ModInfo.xml must be directly inside the",
        "       mod folder, not in a subfolder)",
        "     - XML parse errors from typos in the config files",
        "     - XPath errors if the target node does not exist in your",
        "       game version — compare against vanilla XML files",
        "",
        "DISCLAIMER",
        "-" * 40,
        "Generated by 7 Days to Die Mod Maker.",
        "Not affiliated with The Fun Pimps or 7 Days to Die.",
        "Always back up your saves before installing new mods.",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Item generator
# ---------------------------------------------------------------------------


def generate_item(form_data: dict[str, Any], version_id: str = "v1") -> dict[str, str]:
    """Generate items.xml for a new item mod."""
    item_name = form_data.get("item_name", "modCustomItem").replace(" ", "")
    display_name = form_data.get("display_name", item_name)
    item_type = form_data.get("item_type", "melee_weapon")
    extends = form_data.get("extends", "")
    custom_icon = form_data.get("custom_icon", extends)
    damage = str(form_data.get("damage", "35"))
    item_range = str(form_data.get("range", "2.5"))
    attack_delay = str(form_data.get("attack_delay", "0.56"))
    durability = str(form_data.get("durability", "150"))
    tags = form_data.get("tags", "")

    configs = _configs_root()
    _comment(
        configs,
        f" Item: {item_name} | Type: {item_type} | Target: {version_id} ",
    )
    append = _append_el(configs, "/items")

    item = ET.SubElement(append, "item")
    item.set("name", item_name)

    if extends:
        _prop(item, "Extends", extends)
    if custom_icon:
        _prop(item, "CustomIcon", custom_icon)
    if display_name:
        _prop(item, "CustomIconTint", "1,1,1,1")

    if item_type in ("melee_weapon", "tool"):
        _prop(item, "DisplayType", "toolBelt")
        if tags:
            _prop(item, "Tags", tags)

        action = _prop_class(item, "Action0")
        _prop(action, "Class", "Melee")
        _prop(action, "Damage", damage)
        _prop(action, "AttackRange", item_range)
        _prop(action, "AttackDelay", attack_delay)
        _prop(action, "AttackAngle", "40")

        attrs = _prop_class(item, "Attributes")
        _prop_param(attrs, "DegradationMax", durability)
        _prop_param(attrs, "DegradationBreakPercent", "0")
        _prop_param(attrs, "SellableToTrader", "true")

    elif item_type == "ranged_weapon":
        _prop(item, "DisplayType", "toolBelt")
        if tags:
            _prop(item, "Tags", tags)

        action = _prop_class(item, "Action0")
        _prop(action, "Class", "Shoot")
        _prop(action, "Damage", damage)
        _prop(action, "Range", item_range)
        _prop(action, "MagazineSize", str(form_data.get("magazine_size", "20")))

        attrs = _prop_class(item, "Attributes")
        _prop_param(attrs, "DegradationMax", durability)
        _prop_param(attrs, "SellableToTrader", "true")

    elif item_type == "food":
        _prop(item, "DisplayType", "food")
        if tags:
            _prop(item, "Tags", tags)

        action = _prop_class(item, "Action0")
        _prop(action, "Class", "DrinkLiquid")
        _prop(action, "BuffActions", "buffStationary1min")
        _prop(action, "UseTime", "2")

        attrs = _prop_class(item, "Attributes")
        _prop_param(attrs, "FoodAmount", str(form_data.get("food_amount", "15")))
        _prop_param(attrs, "WaterAmount", str(form_data.get("water_amount", "5")))

    elif item_type == "armor":
        _prop(item, "DisplayType", "armor")
        if tags:
            _prop(item, "Tags", tags)

        attrs = _prop_class(item, "Attributes")
        _prop_param(attrs, "DegradationMax", durability)
        _prop_param(attrs, "ArmorRating", str(form_data.get("armor_rating", "10")))
        _prop_param(attrs, "SellableToTrader", "true")

    else:  # misc
        _prop(item, "DisplayType", "toolBelt")
        if tags:
            _prop(item, "Tags", tags)

    # Localization entry (inline comment — full Localization.txt handled separately)
    loc_lines = [
        "# Paste into Config/Localization.txt (create if it does not exist):",
        "# Key,File,Type,UsedInMainMenu,NoTranslate,english",
        f"# {item_name},Items,Item,,,{display_name}",
    ]

    return {
        "Config/items.xml": _pretty(configs),
        "Config/Localization_hint.txt": "\n".join(loc_lines) + "\n",
    }


# ---------------------------------------------------------------------------
# Recipe generator
# ---------------------------------------------------------------------------


def generate_recipe(form_data: dict[str, Any], version_id: str = "v1") -> dict[str, str]:
    """Generate recipes.xml for a new crafting recipe."""
    recipe_output = form_data.get("recipe_output", "modCustomItem").replace(" ", "")
    output_count = str(form_data.get("output_count", "1"))
    craft_area = form_data.get("craft_area", "workbench")
    craft_time = str(form_data.get("craft_time", "30"))

    # Ingredients: list of dicts with 'name' and 'count', or raw string pairs
    raw_ingredients: list[Any] = form_data.get("ingredients", [])
    ingredients: list[tuple[str, str]] = []
    for ing in raw_ingredients:
        if isinstance(ing, dict):
            name = str(ing.get("name", "")).strip()
            count = str(ing.get("count", "1")).strip()
            if name:
                ingredients.append((name, count))
        elif isinstance(ing, (list, tuple)) and len(ing) >= 2:
            if ing[0]:
                ingredients.append((str(ing[0]).strip(), str(ing[1]).strip()))

    if not ingredients:
        ingredients = [("resourceIronFragment", "10"), ("resourceWood", "20")]

    configs = _configs_root()
    _comment(
        configs,
        f" Recipe for: {recipe_output} | Area: {craft_area} | Target: {version_id} ",
    )
    append = _append_el(configs, "/recipes")

    recipe = ET.SubElement(append, "recipe")
    recipe.set("name", recipe_output)
    recipe.set("count", output_count)
    recipe.set("craft_area", craft_area)
    recipe.set("craft_time", craft_time)

    for ing_name, ing_count in ingredients:
        ing = ET.SubElement(recipe, "ingredient")
        ing.set("name", ing_name)
        ing.set("count", ing_count)

    return {"Config/recipes.xml": _pretty(configs)}


# ---------------------------------------------------------------------------
# Block generator
# ---------------------------------------------------------------------------


def generate_block(form_data: dict[str, Any], version_id: str = "v1") -> dict[str, str]:
    """Generate blocks.xml for a new placeable block."""
    block_name = form_data.get("block_name", "modCustomBlock").replace(" ", "")
    display_name = form_data.get("display_name", block_name)
    extends = form_data.get("extends", "woodMaster")
    custom_icon = form_data.get("custom_icon", extends)
    max_damage = str(form_data.get("max_damage", "500"))
    material = form_data.get("material", "Mwood")
    shape = form_data.get("shape", "Cube")
    stability_glue = form_data.get("stability_glue", False)

    configs = _configs_root()
    _comment(
        configs,
        f" Block: {block_name} | Extends: {extends} | Target: {version_id} ",
    )
    append = _append_el(configs, "/blocks")

    block = ET.SubElement(append, "block")
    block.set("name", block_name)

    if extends:
        _prop(block, "Extends", extends)
    if custom_icon:
        _prop(block, "CustomIcon", custom_icon)
    _prop(block, "MaxDamage", max_damage)
    _prop(block, "Material", material)
    _prop(block, "Shape", shape)
    _prop(block, "DisplayType", "block")
    if stability_glue:
        _prop(block, "StabilityGlue", "true")

    loc_lines = [
        "# Paste into Config/Localization.txt (create if it does not exist):",
        "# Key,File,Type,UsedInMainMenu,NoTranslate,english",
        f"# {block_name},Blocks,Block,,,{display_name}",
    ]

    return {
        "Config/blocks.xml": _pretty(configs),
        "Config/Localization_hint.txt": "\n".join(loc_lines) + "\n",
    }


# ---------------------------------------------------------------------------
# Perk / Progression generator
# ---------------------------------------------------------------------------

_PERK_ICONS = {
    "attSTR": "ui_game_symbol_perk_strength",
    "attPER": "ui_game_symbol_perk_perception",
    "attFOR": "ui_game_symbol_perk_fortitude",
    "attAGI": "ui_game_symbol_perk_agility",
    "attINT": "ui_game_symbol_perk_intelligence",
}


def generate_perk(form_data: dict[str, Any], version_id: str = "v1") -> dict[str, str]:
    """Generate progression.xml for a new perk."""
    perk_name = form_data.get("perk_name", "modCustomPerk").replace(" ", "")
    display_name = form_data.get("display_name", perk_name)
    description = form_data.get("description", "")
    attribute = form_data.get("attribute", "attSTR")
    max_level = int(form_data.get("max_level", 5))
    cost_per_level = str(form_data.get("cost_per_level", 1))
    effect_name = form_data.get("effect_name", "DamageModifier")
    effect_operation = form_data.get("effect_operation", "perc_add")
    effect_value = float(form_data.get("effect_value_per_level", 0.1))
    effect_tags = form_data.get("effect_tags", "melee")
    icon = form_data.get("icon", _PERK_ICONS.get(attribute, "ui_game_symbol_perk_strength"))

    configs = _configs_root()
    _comment(
        configs,
        f" Perk: {perk_name} | Attribute: {attribute} | Levels: {max_level} | Target: {version_id} ",
    )

    # Both A21 and V1.x use /progression/perks
    append = _append_el(configs, "/progression/perks")

    perk = ET.SubElement(append, "perk")
    perk.set("name", perk_name)
    perk.set("max_level", str(max_level))
    perk.set("display_name", display_name)
    perk.set("icon", icon)
    perk.set("icon_color", "1,1,1,1")
    perk.set("desc", description)

    for level_num in range(1, max_level + 1):
        cumulative_value = round(effect_value * level_num, 4)
        level_el = ET.SubElement(perk, "level")
        level_el.set("max_level", str(level_num))
        level_el.set("cost", cost_per_level)
        level_el.set(
            "description",
            f"Rank {level_num}: {effect_name} +{round(cumulative_value * 100, 1)}%",
        )
        # Require the governing attribute at (level_num * 2) to space out unlocks
        level_el.set("requirements", f"{attribute},GTE,{level_num * 2}")

        pe = ET.SubElement(level_el, "passive_effect")
        pe.set("name", effect_name)
        pe.set("operation", effect_operation)
        pe.set("value", str(cumulative_value))
        if effect_tags:
            pe.set("tags", effect_tags)

    return {"Config/progression.xml": _pretty(configs)}


# ---------------------------------------------------------------------------
# Modifier catalogue
# ---------------------------------------------------------------------------

MODIFIERS: list[dict] = [
    # ── POWER ──────────────────────────────────────────────────────────────
    {
        "id": "solar_power_boost",
        "label": "Solar Bank Power Multiplier",
        "category": "Power",
        "description": "Multiplies the power output of solar panels. 2.0 = double output.",
        "property_name": "PowerOutputMultiplier",
        "target_name": "solarBank",
        "xml_file": "items.xml",
        "op": "append",
        "xpath": "/items/item[@name='solarBank']",
        "value_type": "float",
        "vanilla_value": "1.0",
        "value_hint": "Multiplier. 1.0 = vanilla. 2.0 = double output, 0.5 = half.",
        "search_tags": ["solar", "power", "output", "electricity", "energy", "panel"],
    },
    {
        "id": "generator_max_power",
        "label": "Generator Max Power Output",
        "category": "Power",
        "description": "Maximum wattage the generator bank can output.",
        "property_name": "MaxPower",
        "target_name": "generatorBank",
        "xml_file": "items.xml",
        "op": "set",
        "xpath": "/items/item[@name='generatorBank']/property[@name='MaxPower']/@value",
        "value_type": "int",
        "vanilla_value": "12250",
        "value_hint": "Watts. Vanilla: 12,250W. 24500 = double capacity.",
        "search_tags": ["generator", "power", "output", "fuel", "watt"],
    },
    {
        "id": "battery_capacity",
        "label": "Battery Bank Capacity",
        "category": "Power",
        "description": "Storage capacity multiplier for the battery bank.",
        "property_name": "BatteryCapacity",
        "target_name": "batteryBank",
        "xml_file": "items.xml",
        "op": "set",
        "xpath": "/items/item[@name='batteryBank']/property[@name='BatteryCapacity']/@value",
        "value_type": "float",
        "vanilla_value": "1.0",
        "value_hint": "Capacity multiplier. 2.0 = double storage.",
        "search_tags": ["battery", "capacity", "storage", "power"],
    },
    {
        "id": "battery_charge_rate",
        "label": "Battery Bank Charge Rate",
        "category": "Power",
        "description": "Charge rate multiplier for the battery bank.",
        "property_name": "ChargeRate",
        "target_name": "batteryBank",
        "xml_file": "items.xml",
        "op": "set",
        "xpath": "/items/item[@name='batteryBank']/property[@name='ChargeRate']/@value",
        "value_type": "float",
        "vanilla_value": "1.0",
        "value_hint": "Charge rate multiplier. 2.0 = charges twice as fast.",
        "search_tags": ["battery", "charge", "rate", "speed"],
    },
    {
        "id": "electric_fence_power",
        "label": "Electric Fence Power Draw",
        "category": "Power",
        "description": "Watts each electric fence post consumes.",
        "property_name": "RequiredPower",
        "target_name": "electricfencepost",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='electricfencepost']/property[@name='RequiredPower']/@value",
        "value_type": "int",
        "vanilla_value": "5",
        "value_hint": "Watts per post. Vanilla: 5W. Lower = cheaper to run.",
        "search_tags": ["fence", "electric", "power", "draw", "watt"],
    },
    {
        "id": "dart_trap_power",
        "label": "Dart Trap Power Draw",
        "category": "Power",
        "description": "Watts the dart trap consumes while running.",
        "property_name": "RequiredPower",
        "target_name": "dartTrap",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='dartTrap']/property[@name='RequiredPower']/@value",
        "value_type": "int",
        "vanilla_value": "10",
        "value_hint": "Watts. Vanilla: 10W.",
        "search_tags": ["dart", "trap", "power", "draw", "watt"],
    },
    {
        "id": "auto_turret_power",
        "label": "Auto Turret Power Draw",
        "category": "Power",
        "description": "Watts the auto turret consumes while active.",
        "property_name": "RequiredPower",
        "target_name": "autoTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='autoTurret']/property[@name='RequiredPower']/@value",
        "value_type": "int",
        "vanilla_value": "15",
        "value_hint": "Watts. Vanilla: 15W.",
        "search_tags": ["turret", "auto", "power", "draw", "watt"],
    },
    # ── TURRETS & TRAPS ─────────────────────────────────────────────────────
    {
        "id": "auto_turret_range",
        "label": "Auto Turret Detection Range",
        "category": "Turrets & Traps",
        "description": "Max distance (metres) the auto turret detects enemies.",
        "property_name": "MaxDistance",
        "target_name": "autoTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='autoTurret']/property[@name='MaxDistance']/@value",
        "value_type": "float",
        "vanilla_value": "30",
        "value_hint": "Metres. Vanilla: 30m. 60 = twice the range.",
        "search_tags": ["turret", "auto", "range", "distance", "detection", "sight"],
    },
    {
        "id": "auto_turret_turn_speed",
        "label": "Auto Turret Rotation Speed",
        "category": "Turrets & Traps",
        "description": "How fast the auto turret rotates to track targets.",
        "property_name": "TurnSpeed",
        "target_name": "autoTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='autoTurret']/property[@name='TurnSpeed']/@value",
        "value_type": "float",
        "vanilla_value": "22.5",
        "value_hint": "Degrees/second. Vanilla: 22.5\u00b0/s. Higher = snappier tracking.",
        "search_tags": ["turret", "auto", "rotation", "turn", "speed", "track"],
    },
    {
        "id": "shotgun_turret_range",
        "label": "Shotgun Turret Detection Range",
        "category": "Turrets & Traps",
        "description": "Max distance (metres) the shotgun turret detects enemies.",
        "property_name": "MaxDistance",
        "target_name": "shotgunTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='shotgunTurret']/property[@name='MaxDistance']/@value",
        "value_type": "float",
        "vanilla_value": "15",
        "value_hint": "Metres. Vanilla: 15m.",
        "search_tags": ["turret", "shotgun", "range", "distance", "detection"],
    },
    {
        "id": "shotgun_turret_damage",
        "label": "Shotgun Turret Pellet Damage",
        "category": "Turrets & Traps",
        "description": "Damage per pellet fired. 8 pellets per burst at vanilla.",
        "property_name": "EntityDamage",
        "target_name": "shotgunTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='shotgunTurret']/property[@name='EntityDamage']/@value",
        "value_type": "int",
        "vanilla_value": "9",
        "value_hint": "Damage per pellet. Vanilla: 9. 8 pellets per burst = 72 total at vanilla.",
        "search_tags": ["turret", "shotgun", "damage", "pellet", "burst", "dps"],
    },
    {
        "id": "shotgun_turret_burst",
        "label": "Shotgun Turret Burst Interval",
        "category": "Turrets & Traps",
        "description": "Seconds between bursts. Lower = faster fire.",
        "property_name": "BurstFireRate",
        "target_name": "shotgunTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='shotgunTurret']/property[@name='BurstFireRate']/@value",
        "value_type": "float",
        "vanilla_value": "0.61",
        "value_hint": "Seconds between bursts. Vanilla: 0.61s. 0.3 = twice as fast.",
        "search_tags": ["turret", "shotgun", "fire", "rate", "burst", "speed", "dps"],
    },
    {
        "id": "dart_trap_fire_rate",
        "label": "Dart Trap Fire Rate",
        "category": "Turrets & Traps",
        "description": "Seconds between dart shots. Lower = faster.",
        "property_name": "BurstFireRate",
        "target_name": "dartTrap",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='dartTrap']/property[@name='BurstFireRate']/@value",
        "value_type": "float",
        "vanilla_value": "0.5",
        "value_hint": "Seconds per dart. Vanilla: 0.5s (2/sec). 0.25 = 4/sec.",
        "search_tags": ["dart", "trap", "fire", "rate", "speed", "dps"],
    },
    {
        "id": "electric_fence_damage",
        "label": "Electric Fence Shock Damage",
        "category": "Turrets & Traps",
        "description": "Fraction of base damage dealt by the electric fence.",
        "property_name": "DamageReceived",
        "target_name": "electricfencepost",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='electricfencepost']/property[@name='DamageReceived']/@value",
        "value_type": "float",
        "vanilla_value": "0.5",
        "value_hint": "Fraction of base damage. Vanilla: 0.5 (50%). 1.0 = full damage.",
        "search_tags": ["fence", "electric", "damage", "shock", "trap"],
    },
    # ── WORKSTATIONS ────────────────────────────────────────────────────────
    {
        "id": "forge_durability",
        "label": "Forge Durability",
        "category": "Workstations",
        "description": "Hit points of the forge block.",
        "property_name": "MaxDamage",
        "target_name": "forge",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='forge']/property[@name='MaxDamage']/@value",
        "value_type": "int",
        "vanilla_value": "800",
        "value_hint": "Hit points. Vanilla: 800. 8000 = nearly indestructible.",
        "search_tags": ["forge", "durability", "hp", "health", "workstation"],
    },
    {
        "id": "campfire_durability",
        "label": "Campfire Durability",
        "category": "Workstations",
        "description": "Hit points of the campfire block.",
        "property_name": "MaxDamage",
        "target_name": "campfire",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='campfire']/property[@name='MaxDamage']/@value",
        "value_type": "int",
        "vanilla_value": "100",
        "value_hint": "Hit points. Vanilla: 100.",
        "search_tags": ["campfire", "durability", "hp", "health", "fire", "cook"],
    },
    {
        "id": "cement_mixer_durability",
        "label": "Cement Mixer Durability",
        "category": "Workstations",
        "description": "Hit points of the cement mixer block.",
        "property_name": "MaxDamage",
        "target_name": "cementMixer",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='cementMixer']/property[@name='MaxDamage']/@value",
        "value_type": "int",
        "vanilla_value": "800",
        "value_hint": "Hit points. Vanilla: 800.",
        "search_tags": ["cement", "mixer", "durability", "hp", "workstation"],
    },
    {
        "id": "chemistry_station_durability",
        "label": "Chemistry Station Durability",
        "category": "Workstations",
        "description": "Hit points of the chemistry station block.",
        "property_name": "MaxDamage",
        "target_name": "chemistryStation",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='chemistryStation']/property[@name='MaxDamage']/@value",
        "value_type": "int",
        "vanilla_value": "800",
        "value_hint": "Hit points. Vanilla: 800.",
        "search_tags": ["chemistry", "station", "durability", "hp", "workstation"],
    },
    {
        "id": "forge_heat",
        "label": "Forge Heat Map Strength",
        "category": "Workstations",
        "description": "Heat signature that attracts zombie hordes. 0 = no risk.",
        "property_name": "HeatMapStrength",
        "target_name": "forge",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='forge']/property[@name='HeatMapStrength']/@value",
        "value_type": "int",
        "vanilla_value": "6",
        "value_hint": "Heat units. Vanilla: 6. 0 = no horde attraction.",
        "search_tags": ["forge", "heat", "map", "horde", "zombie", "attract", "stealth"],
    },
    {
        "id": "campfire_heat",
        "label": "Campfire Heat Map Strength",
        "category": "Workstations",
        "description": "Heat signature from the campfire during cooking.",
        "property_name": "HeatMapStrength",
        "target_name": "campfire",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='campfire']/property[@name='HeatMapStrength']/@value",
        "value_type": "int",
        "vanilla_value": "5",
        "value_hint": "Vanilla: 5. 0 = stealth cooking.",
        "search_tags": ["campfire", "heat", "map", "horde", "zombie", "stealth", "fire"],
    },
    {
        "id": "cement_mixer_heat",
        "label": "Cement Mixer Heat Map Strength",
        "category": "Workstations",
        "description": "Heat signature from the cement mixer while running.",
        "property_name": "HeatMapStrength",
        "target_name": "cementMixer",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='cementMixer']/property[@name='HeatMapStrength']/@value",
        "value_type": "int",
        "vanilla_value": "5",
        "value_hint": "Vanilla: 5.",
        "search_tags": ["cement", "mixer", "heat", "map", "horde", "zombie"],
    },
    {
        "id": "chemistry_station_heat",
        "label": "Chemistry Station Heat Map Strength",
        "category": "Workstations",
        "description": "Heat signature from the chemistry station while running.",
        "property_name": "HeatMapStrength",
        "target_name": "chemistryStation",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='chemistryStation']/property[@name='HeatMapStrength']/@value",
        "value_type": "int",
        "vanilla_value": "5",
        "value_hint": "Vanilla: 5.",
        "search_tags": ["chemistry", "station", "heat", "map", "horde", "zombie"],
    },
    # ── ECONOMY ─────────────────────────────────────────────────────────────
    {
        "id": "generator_value",
        "label": "Generator Bank Trader Value",
        "category": "Economy",
        "description": "Duke value assigned to the generator bank by traders.",
        "property_name": "EconomicValue",
        "target_name": "generatorBankA",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='generatorBankA']/property[@name='EconomicValue']/@value",
        "value_type": "int",
        "vanilla_value": "500",
        "value_hint": "Dukes. Vanilla: 500.",
        "search_tags": ["generator", "value", "economy", "trader", "duke", "sell", "price"],
    },
    {
        "id": "solar_bank_value",
        "label": "Solar Bank Trader Value",
        "category": "Economy",
        "description": "Duke value assigned to the solar bank by traders.",
        "property_name": "EconomicValue",
        "target_name": "solarBank",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='solarBank']/property[@name='EconomicValue']/@value",
        "value_type": "int",
        "vanilla_value": "2000",
        "value_hint": "Dukes. Vanilla: 2,000.",
        "search_tags": ["solar", "value", "economy", "trader", "duke", "sell", "price"],
    },
    {
        "id": "auto_turret_value",
        "label": "Auto Turret Trader Value",
        "category": "Economy",
        "description": "Duke value assigned to the auto turret by traders.",
        "property_name": "EconomicValue",
        "target_name": "autoTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='autoTurret']/property[@name='EconomicValue']/@value",
        "value_type": "int",
        "vanilla_value": "3000",
        "value_hint": "Dukes. Vanilla: 3,000.",
        "search_tags": ["turret", "auto", "value", "economy", "trader", "duke"],
    },
    {
        "id": "shotgun_turret_value",
        "label": "Shotgun Turret Trader Value",
        "category": "Economy",
        "description": "Duke value assigned to the shotgun turret by traders.",
        "property_name": "EconomicValue",
        "target_name": "shotgunTurret",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='shotgunTurret']/property[@name='EconomicValue']/@value",
        "value_type": "int",
        "vanilla_value": "2500",
        "value_hint": "Dukes. Vanilla: 2,500.",
        "search_tags": ["turret", "shotgun", "value", "economy", "trader", "duke"],
    },
    {
        "id": "chemistry_station_value",
        "label": "Chemistry Station Trader Value",
        "category": "Economy",
        "description": "Duke value assigned to the chemistry station by traders.",
        "property_name": "EconomicValue",
        "target_name": "chemistryStation",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='chemistryStation']/property[@name='EconomicValue']/@value",
        "value_type": "int",
        "vanilla_value": "5000",
        "value_hint": "Dukes. Vanilla: 5,000.",
        "search_tags": ["chemistry", "station", "value", "economy", "trader", "duke"],
    },
    {
        "id": "forge_value",
        "label": "Forge Trader Value",
        "category": "Economy",
        "description": "Duke value assigned to the forge by traders.",
        "property_name": "EconomicValue",
        "target_name": "forge",
        "xml_file": "blocks.xml",
        "op": "set",
        "xpath": "/blocks/block[@name='forge']/property[@name='EconomicValue']/@value",
        "value_type": "int",
        "vanilla_value": "1000",
        "value_hint": "Dukes. Vanilla: 1,000.",
        "search_tags": ["forge", "value", "economy", "trader", "duke"],
    },
]

MODIFIER_MAP: dict[str, dict] = {m["id"]: m for m in MODIFIERS}
MODIFIER_CATEGORIES: list[str] = list(dict.fromkeys(m["category"] for m in MODIFIERS))


# ---------------------------------------------------------------------------
# Modifier generator
# ---------------------------------------------------------------------------


def generate_modifier(form_data: dict[str, Any], version_id: str = "v1") -> dict[str, str]:
    """Generate a single-property mod XML from the MODIFIERS catalogue."""
    mod_id = form_data.get("modifier_id", "")
    modifier = MODIFIER_MAP.get(mod_id)
    if modifier is None:
        raise ValueError(f"Unknown modifier_id: {mod_id!r}")
    value = str(form_data.get("value", modifier["vanilla_value"])).strip()
    configs = _configs_root()
    _comment(
        configs,
        (
            f" {modifier['label']} | {modifier['target_name']}.{modifier['property_name']}"
            f" ({modifier['xml_file']}) | vanilla: {modifier['vanilla_value']} \u2192 {value}"
            f" | 7DtD {GAME_VERSION_LABEL} "
        ),
    )
    if modifier["op"] == "append":
        append_el = _append_el(configs, modifier["xpath"])
        _prop(append_el, modifier["property_name"], value)
    else:
        _set_el(configs, modifier["xpath"], value)
    return {f"Config/{modifier['xml_file']}": _pretty(configs)}


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


_GENERATORS = {
    "item": generate_item,
    "recipe": generate_recipe,
    "block": generate_block,
    "perk": generate_perk,
    "modifier": generate_modifier,
}


def generate_mod_files(
    mod_type: str, form_data: dict[str, Any], version_id: str = "v1"
) -> dict[str, str]:
    """Return a dict of {relative_path: content} for the mod's config files."""
    gen = _GENERATORS.get(mod_type)
    if gen is None:
        raise ValueError(f"Unknown mod type: {mod_type!r}")
    return gen(form_data, version_id)


# ---------------------------------------------------------------------------
# ZIP builder
# ---------------------------------------------------------------------------


def build_zip(
    mod_folder_name: str,
    mod_info_xml: str,
    config_files: dict[str, str],
    readme_txt: str,
) -> bytes:
    """Build and return a ZIP file as bytes.

    Structure inside ZIP:
        {mod_folder_name}/
            ModInfo.xml
            README.txt
            Config/
                *.xml
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{mod_folder_name}/ModInfo.xml", mod_info_xml)
        zf.writestr(f"{mod_folder_name}/README.txt", readme_txt)
        for rel_path, content in config_files.items():
            zf.writestr(f"{mod_folder_name}/{rel_path}", content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS: dict[str, list[dict[str, Any]]] = {
    "item": [
        {
            "id": "basic_melee",
            "name": "Basic Melee Weapon",
            "description": "A simple melee weapon extending the iron pickaxe.",
            "defaults": {
                "item_type": "melee_weapon",
                "extends": "meleeToolPickaxeT1IronPickaxe",
                "custom_icon": "meleeToolPickaxeT1IronPickaxe",
                "damage": "35",
                "range": "2.5",
                "attack_delay": "0.56",
                "durability": "150",
                "tags": "melee",
            },
        },
        {
            "id": "healing_food",
            "name": "Healing Food Item",
            "description": "A consumable food item that restores hunger and water.",
            "defaults": {
                "item_type": "food",
                "extends": "foodBaconAndEggs",
                "custom_icon": "foodBaconAndEggs",
                "food_amount": "20",
                "water_amount": "10",
                "durability": "1",
                "tags": "food",
            },
        },
        {
            "id": "mining_tool",
            "name": "Mining Tool",
            "description": "A high-damage mining tool for harvesting resources.",
            "defaults": {
                "item_type": "tool",
                "extends": "meleeToolPickaxeT2SteelPickaxe",
                "custom_icon": "meleeToolPickaxeT2SteelPickaxe",
                "damage": "50",
                "range": "2.5",
                "attack_delay": "0.56",
                "durability": "300",
                "tags": "tool,melee",
            },
        },
        {
            "id": "light_armor",
            "name": "Light Armor Piece",
            "description": "A lightweight armor piece providing modest protection.",
            "defaults": {
                "item_type": "armor",
                "extends": "armorLeatherChest",
                "custom_icon": "armorLeatherChest",
                "armor_rating": "15",
                "durability": "200",
                "tags": "armor",
            },
        },
    ],
    "recipe": [
        {
            "id": "workbench_recipe",
            "name": "Simple Workbench Recipe",
            "description": "A recipe crafted at the workbench using common resources.",
            "defaults": {
                "craft_area": "workbench",
                "craft_time": "30",
                "output_count": "1",
                "ingredients": [
                    {"name": "resourceIronFragment", "count": "10"},
                    {"name": "resourceWood", "count": "20"},
                    {"name": "resourceOil", "count": "5"},
                ],
            },
        },
        {
            "id": "handcraft_recipe",
            "name": "Field Craft Recipe",
            "description": "A recipe that can be crafted in the player inventory.",
            "defaults": {
                "craft_area": "player",
                "craft_time": "10",
                "output_count": "1",
                "ingredients": [
                    {"name": "resourceWood", "count": "5"},
                    {"name": "resourceRockSmall", "count": "3"},
                ],
            },
        },
    ],
    "block": [
        {
            "id": "storage_crate",
            "name": "Storage Crate",
            "description": "A large wooden storage container block.",
            "defaults": {
                "extends": "cntWoodCrate",
                "custom_icon": "cntWoodCrate",
                "max_damage": "500",
                "material": "Mwood",
                "shape": "Cube",
                "stability_glue": False,
            },
        },
        {
            "id": "decorative_block",
            "name": "Decorative Block",
            "description": "A decorative block for base building.",
            "defaults": {
                "extends": "woodMaster",
                "custom_icon": "woodMaster",
                "max_damage": "300",
                "material": "Mwood",
                "shape": "Cube",
                "stability_glue": True,
            },
        },
    ],
    "perk": [
        {
            "id": "passive_stat_perk",
            "name": "Passive Stat Perk",
            "description": "A 5-rank perk that passively increases melee damage.",
            "defaults": {
                "attribute": "attSTR",
                "max_level": "5",
                "cost_per_level": "1",
                "effect_name": "DamageModifier",
                "effect_operation": "perc_add",
                "effect_value_per_level": "0.1",
                "effect_tags": "melee",
            },
        },
        {
            "id": "crafting_speed_perk",
            "name": "Crafting Speed Perk",
            "description": "A 3-rank perk that reduces crafting time.",
            "defaults": {
                "attribute": "attINT",
                "max_level": "3",
                "cost_per_level": "1",
                "effect_name": "CraftingTime",
                "effect_operation": "perc_add",
                "effect_value_per_level": "-0.1",
                "effect_tags": "",
            },
        },
    ],
    "modifier": [
        {
            "id": "solar_boost",
            "name": "Solar Power Boost",
            "description": "Double the power output of all solar banks.",
            "defaults": {"modifier_id": "solar_power_boost", "value": "2.0"},
        },
        {
            "id": "extended_turret_range",
            "name": "Extended Auto Turret Range",
            "description": "Double the auto turret's detection range.",
            "defaults": {"modifier_id": "auto_turret_range", "value": "60"},
        },
        {
            "id": "stealth_forge",
            "name": "Stealth Forge",
            "description": "Remove forge heat signature to prevent horde attraction.",
            "defaults": {"modifier_id": "forge_heat", "value": "0"},
        },
    ],
}
