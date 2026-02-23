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

from .versions import VersionDef, get_version

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
    version: str = "1.0.0",
    website: str = "",
) -> str:
    root = ET.Element("xml")
    ET.SubElement(root, "Name").set("value", name)
    ET.SubElement(root, "DisplayName").set("value", display_name or name)
    ET.SubElement(root, "Version").set("value", version)
    ET.SubElement(root, "Description").set("value", description)
    ET.SubElement(root, "Author").set("value", author)
    ET.SubElement(root, "Website").set("value", website)
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
# Modifier generator
# ---------------------------------------------------------------------------


def generate_modifier(form_data: dict[str, Any], version_id: str = "v1") -> dict[str, str]:
    """Generate a modifier XML for solar power, zombie HP, loot, or recipe cost."""
    modifier_type = form_data.get("modifier_type", "solar_power")

    if modifier_type == "solar_power":
        return _gen_solar_modifier(form_data, version_id)
    elif modifier_type == "zombie_hp":
        return _gen_zombie_hp_modifier(form_data, version_id)
    elif modifier_type == "loot_multiplier":
        return _gen_loot_modifier(form_data, version_id)
    elif modifier_type == "recipe_cost":
        return _gen_recipe_cost_modifier(form_data, version_id)
    else:
        raise ValueError(f"Unknown modifier_type: {modifier_type!r}")


# --- Solar power ---

# Approximate vanilla base wattage values per tier (community-sourced estimates).
# Actual values may vary; README advises users to verify against vanilla files.
_SOLAR_BANKS = [
    ("solarBankRankedT1Damaged", 15),
    ("solarBankRankedT1", 35),
    ("solarBankRankedT2", 70),
    ("solarBankRankedT3", 110),
]


def _gen_solar_modifier(form_data: dict[str, Any], version_id: str) -> dict[str, str]:
    multiplier = float(form_data.get("multiplier", 2.0))
    configs = _configs_root()
    _comment(
        configs,
        (
            f" Solar Power Modifier — {multiplier}x output | Target: {version_id} \n"
            "  Base values below are approximate vanilla estimates.\n"
            "  Verify against Config/blocks.xml in your game installation.\n"
            "  For V1.x the property name is PowerOutput.\n"
            "  For A21 the equivalent is the 'electricbase' property. "
        ),
    )
    for block_name, base_w in _SOLAR_BANKS:
        new_w = int(round(base_w * multiplier))
        _comment(configs, f" {block_name}: ~{base_w}W base → {new_w}W ({multiplier}x) ")
        _set_el(
            configs,
            f"/blocks/block[@name='{block_name}']/property[@name='PowerOutput']/@value",
            str(new_w),
        )
    return {"Config/blocks.xml": _pretty(configs)}


# --- Zombie HP ---


def _gen_zombie_hp_modifier(form_data: dict[str, Any], version_id: str) -> dict[str, str]:
    multiplier = float(form_data.get("multiplier", 2.0))

    # Approximate vanilla base HP (community-sourced).
    zombie_hp_defaults = [
        ("ZombieBase", 100),
        ("ZombieFeralBase", 200),
        ("ZombieRadiatedBase", 500),
        ("ZombieBear", 2000),
        ("AnimalBoar", 200),
    ]

    configs = _configs_root()
    _comment(
        configs,
        (
            f" Zombie HP Modifier — {multiplier}x | Target: {version_id} \n"
            "  Base values are approximate. Verify against Config/entityclasses.xml\n"
            "  in your game installation before deploying.\n"
            "  If 'ZombieBase' does not exist in your version, add entries for\n"
            "  individual zombie names from entityclasses.xml. "
        ),
    )
    for entity_name, base_hp in zombie_hp_defaults:
        new_hp = int(round(base_hp * multiplier))
        _comment(configs, f" {entity_name}: ~{base_hp} HP base → {new_hp} HP ({multiplier}x) ")
        _set_el(
            configs,
            f"/entity_classes/entity_class[@name='{entity_name}']/property[@name='MaxHealth']/@value",
            str(new_hp),
        )
    return {"Config/entityclasses.xml": _pretty(configs)}


# --- Loot multiplier ---


def _gen_loot_modifier(form_data: dict[str, Any], version_id: str) -> dict[str, str]:
    multiplier = float(form_data.get("multiplier", 2.0))

    # Common loot container names (approximations — verify in your installation).
    containers = [
        ("supplyCrate", "4,6"),
        ("traderCargo01", "3,5"),
        ("zBackpack", "1,3"),
        ("droppedBagPlayer", "2,4"),
    ]

    configs = _configs_root()

    if version_id == "a21":
        file_note = "loot.xml — single file for A21"
    else:
        file_note = (
            "loot.xml — V1.x splits loot by biome. Duplicate this pattern\n"
            "  in loot_wasteland.xml, loot_burned.xml, loot_snow.xml, etc.\n"
            "  for full biome coverage."
        )

    _comment(
        configs,
        (
            f" Loot Multiplier — ~{multiplier}x | Target: {version_id} \n"
            f"  File target: {file_note}\n"
            "  Count ranges like '4,6' mean 'pick between 4 and 6 items'.\n"
            "  These targets are common containers — verify names against\n"
            "  Config/loot.xml in your installation. "
        ),
    )

    for container_name, base_count in containers:
        # Scale the count range by the multiplier
        parts = base_count.split(",")
        try:
            lo = int(round(int(parts[0]) * multiplier))
            hi = int(round(int(parts[1]) * multiplier)) if len(parts) > 1 else lo
        except (ValueError, IndexError):
            lo, hi = 2, 4
        new_count = f"{lo},{hi}"
        _comment(configs, f" {container_name}: {base_count} → {new_count} ")
        _set_el(
            configs,
            f"/lootcontainers/lootcontainer[@name='{container_name}']/lootgroup/@count",
            new_count,
        )

    return {"Config/loot.xml": _pretty(configs)}


# --- Recipe cost modifier ---


def _gen_recipe_cost_modifier(form_data: dict[str, Any], version_id: str) -> dict[str, str]:
    recipe_name = form_data.get("target_recipe_name", "").strip()
    ingredient_name = form_data.get("ingredient_name", "").strip()
    new_count = str(form_data.get("new_count", "5"))

    configs = _configs_root()

    if recipe_name and ingredient_name:
        _comment(
            configs,
            (
                f" Recipe Cost Modifier | Target: {version_id} \n"
                f"  Recipe: {recipe_name}, Ingredient: {ingredient_name} → count {new_count} "
            ),
        )
        _set_el(
            configs,
            f"/recipes/recipe[@name='{recipe_name}']/ingredient[@name='{ingredient_name}']/@count",
            new_count,
        )
    elif ingredient_name:
        _comment(
            configs,
            (
                f" Recipe Cost Modifier — ALL recipes using {ingredient_name} | Target: {version_id} \n"
                "  WARNING: This sets the count for every recipe that uses this ingredient.\n"
                "  Consider targeting specific recipes by name instead. "
            ),
        )
        _set_el(
            configs,
            f"/recipes/recipe/ingredient[@name='{ingredient_name}']/@count",
            new_count,
        )
    else:
        _comment(configs, " Recipe Cost Modifier — no ingredient specified, no changes generated ")

    return {"Config/recipes.xml": _pretty(configs)}


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
            "description": "Multiplies the power output of all solar bank tiers.",
            "defaults": {
                "modifier_type": "solar_power",
                "multiplier": "2.0",
            },
        },
        {
            "id": "zombie_hp",
            "name": "Zombie HP Multiplier",
            "description": "Multiplies the max health of zombie base classes.",
            "defaults": {
                "modifier_type": "zombie_hp",
                "multiplier": "2.0",
            },
        },
        {
            "id": "loot_boost",
            "name": "Loot Multiplier",
            "description": "Increases item count ranges in common loot containers.",
            "defaults": {
                "modifier_type": "loot_multiplier",
                "multiplier": "2.0",
            },
        },
        {
            "id": "cheaper_recipe",
            "name": "Cheaper Recipe",
            "description": "Reduces the cost of a specific ingredient in a recipe.",
            "defaults": {
                "modifier_type": "recipe_cost",
                "target_recipe_name": "",
                "ingredient_name": "resourceIronFragment",
                "new_count": "5",
            },
        },
    ],
}
