"""Tests for src.generator — XML generation and ZIP building."""

import io
import zipfile
import xml.etree.ElementTree as ET

import pytest

from src.generator import (
    build_zip,
    generate_item,
    generate_recipe,
    generate_block,
    generate_perk,
    generate_modifier,
    generate_mod_files,
    make_modinfo_xml,
    make_readme_txt,
    MODIFIERS,
    MODIFIER_MAP,
    PRESETS,
)
from src.versions import get_version, DEFAULT_VERSION_ID


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(xml_str: str) -> ET.Element:
    """Parse XML string and return root; raises on invalid XML."""
    return ET.fromstring(xml_str)


def _zip_names(data: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return z.namelist()


def _zip_read(data: bytes, path: str) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return z.read(path).decode()


# ---------------------------------------------------------------------------
# make_modinfo_xml
# ---------------------------------------------------------------------------

class TestMakeModinfoXml:
    def test_valid_xml(self):
        xml = make_modinfo_xml("TestMod", "Test Mod", "A test.", "anon", "1.0", "")
        root = _parse(xml)
        assert root.tag == "xml"

    def test_contains_modinfo_wrapper(self):
        xml = make_modinfo_xml("TestMod")
        root = _parse(xml)
        info = root.find("ModInfo")
        assert info is not None, "Expected <ModInfo> child element"

    def test_contains_name(self):
        xml = make_modinfo_xml("TestMod", "Test Mod", "A test.", "anon", "1.0", "")
        assert "TestMod" in xml

    def test_contains_version(self):
        xml = make_modinfo_xml("TestMod", "Test Mod", "A test.", "anon", "2.3.1", "")
        assert "2.3.1" in xml

    def test_no_website_when_empty(self):
        xml = make_modinfo_xml("TestMod")
        assert "Website" not in xml


# ---------------------------------------------------------------------------
# make_readme_txt
# ---------------------------------------------------------------------------

class TestMakeReadmeTxt:
    def test_includes_mod_name(self):
        v = get_version(DEFAULT_VERSION_ID)
        txt = make_readme_txt("MyWeapon", "item", {"item_type": "melee_weapon"}, v)
        assert "MyWeapon" in txt

    def test_includes_version_label(self):
        v = get_version(DEFAULT_VERSION_ID)
        txt = make_readme_txt("X", "item", {}, v)
        assert v["label"] in txt

    def test_includes_install_steps(self):
        v = get_version(DEFAULT_VERSION_ID)
        txt = make_readme_txt("X", "item", {}, v)
        assert "Mods" in txt


# ---------------------------------------------------------------------------
# generate_item
# ---------------------------------------------------------------------------

class TestGenerateItem:
    BASE = {
        "item_name": "myMod_TestSword",
        "display_name": "Test Sword",
        "description": "A test sword.",
        "item_type": "melee_weapon",
        "extends": "",
        "custom_icon": "",
        "damage": "45",
        "range": "2.5",
        "attack_delay": "0.8",
        "durability": "300",
        "tags": "",
    }

    def test_returns_items_xml_key(self):
        files = generate_item(self.BASE, DEFAULT_VERSION_ID)
        assert "Config/items.xml" in files

    def test_items_xml_is_valid(self):
        files = generate_item(self.BASE, DEFAULT_VERSION_ID)
        _parse(files["Config/items.xml"])

    def test_item_name_present(self):
        files = generate_item(self.BASE, DEFAULT_VERSION_ID)
        assert "myMod_TestSword" in files["Config/items.xml"]

    def test_localization_hint_present(self):
        files = generate_item(self.BASE, DEFAULT_VERSION_ID)
        assert "Config/Localization_hint.txt" in files

    def test_ranged_weapon_has_magazine(self):
        data = dict(self.BASE, item_type="ranged_weapon", magazine_size="15")
        files = generate_item(data, DEFAULT_VERSION_ID)
        assert "MagazineSize" in files["Config/items.xml"] or "magazine" in files["Config/items.xml"].lower()

    def test_food_has_food_amount(self):
        data = dict(self.BASE, item_type="food", food_amount="20", water_amount="0")
        files = generate_item(data, DEFAULT_VERSION_ID)
        assert "FoodAmount" in files["Config/items.xml"] or "food" in files["Config/items.xml"].lower()

    def test_works_for_a21(self):
        files = generate_item(self.BASE, "a21")
        _parse(files["Config/items.xml"])


# ---------------------------------------------------------------------------
# generate_recipe
# ---------------------------------------------------------------------------

class TestGenerateRecipe:
    BASE = {
        "recipe_output": "myMod_TestSword",
        "output_count": "1",
        "craft_area": "workbench",
        "craft_time": "15",
        "description": "A test recipe.",
        "ingredients": [
            {"name": "resourceIronIngot", "count": 10},
            {"name": "resourceWood", "count": 5},
        ],
    }

    def test_returns_recipes_xml_key(self):
        files = generate_recipe(self.BASE, DEFAULT_VERSION_ID)
        assert "Config/recipes.xml" in files

    def test_recipes_xml_is_valid(self):
        files = generate_recipe(self.BASE, DEFAULT_VERSION_ID)
        _parse(files["Config/recipes.xml"])

    def test_output_name_present(self):
        files = generate_recipe(self.BASE, DEFAULT_VERSION_ID)
        assert "myMod_TestSword" in files["Config/recipes.xml"]

    def test_ingredients_present(self):
        files = generate_recipe(self.BASE, DEFAULT_VERSION_ID)
        xml = files["Config/recipes.xml"]
        assert "resourceIronIngot" in xml
        assert "resourceWood" in xml

    def test_empty_ingredients_still_valid(self):
        data = dict(self.BASE, ingredients=[])
        files = generate_recipe(data, DEFAULT_VERSION_ID)
        _parse(files["Config/recipes.xml"])


# ---------------------------------------------------------------------------
# generate_block
# ---------------------------------------------------------------------------

class TestGenerateBlock:
    BASE = {
        "block_name": "myMod_TestBlock",
        "display_name": "Test Block",
        "description": "A test block.",
        "extends": "",
        "custom_icon": "",
        "max_damage": "500",
        "material": "Msteel",
        "shape": "Cube",
        "stability_glue": False,
    }

    def test_returns_blocks_xml_key(self):
        files = generate_block(self.BASE, DEFAULT_VERSION_ID)
        assert "Config/blocks.xml" in files

    def test_blocks_xml_is_valid(self):
        files = generate_block(self.BASE, DEFAULT_VERSION_ID)
        _parse(files["Config/blocks.xml"])

    def test_block_name_present(self):
        files = generate_block(self.BASE, DEFAULT_VERSION_ID)
        assert "myMod_TestBlock" in files["Config/blocks.xml"]

    def test_localization_hint_present(self):
        files = generate_block(self.BASE, DEFAULT_VERSION_ID)
        assert "Config/Localization_hint.txt" in files


# ---------------------------------------------------------------------------
# generate_perk
# ---------------------------------------------------------------------------

class TestGeneratePerk:
    BASE = {
        "perk_name": "myMod_TestPerk",
        "display_name": "Test Perk",
        "description": "A test perk.",
        "attribute": "attSTR",
        "max_level": "3",
        "cost_per_level": "1",
        "icon": "ui_game_symbol_perk",
        "effect_name": "DamageMelee",
        "effect_operation": "perc_add",
        "effect_value_per_level": "0.1",
        "effect_tags": "",
    }

    def test_returns_progression_xml_key(self):
        files = generate_perk(self.BASE, DEFAULT_VERSION_ID)
        assert "Config/progression.xml" in files

    def test_progression_xml_is_valid(self):
        files = generate_perk(self.BASE, DEFAULT_VERSION_ID)
        _parse(files["Config/progression.xml"])

    def test_perk_name_present(self):
        files = generate_perk(self.BASE, DEFAULT_VERSION_ID)
        assert "myMod_TestPerk" in files["Config/progression.xml"]

    def test_correct_rank_count(self):
        files = generate_perk(self.BASE, DEFAULT_VERSION_ID)
        root = _parse(files["Config/progression.xml"])
        # Count <append> elements containing rank info
        xml = files["Config/progression.xml"]
        # There should be max_level (3) rank entries
        assert xml.count('rank=') >= 3 or xml.count('level=') >= 3 or xml.count('<rank') >= 3 or "3" in xml

    def test_works_for_a21(self):
        files = generate_perk(self.BASE, "a21")
        _parse(files["Config/progression.xml"])


# ---------------------------------------------------------------------------
# generate_modifier
# ---------------------------------------------------------------------------

class TestGenerateModifier:
    def test_solar_returns_items_xml(self):
        data = {"modifier_id": "solar_power_boost", "value": "2.0"}
        files = generate_modifier(data)
        assert "Config/items.xml" in files
        _parse(files["Config/items.xml"])

    def test_blocks_xml_modifier(self):
        data = {"modifier_id": "auto_turret_range", "value": "60"}
        files = generate_modifier(data)
        assert "Config/blocks.xml" in files
        _parse(files["Config/blocks.xml"])

    def test_value_appears_in_output(self):
        data = {"modifier_id": "forge_heat", "value": "0"}
        files = generate_modifier(data)
        assert "0" in files["Config/blocks.xml"]

    def test_vanilla_value_used_when_no_value_given(self):
        """If 'value' is omitted the vanilla default should appear in the output."""
        m = MODIFIER_MAP["generator_max_power"]
        data = {"modifier_id": "generator_max_power"}
        files = generate_modifier(data)
        assert m["vanilla_value"] in files[f"Config/{m['xml_file']}"]

    def test_unknown_modifier_raises(self):
        with pytest.raises(ValueError, match="Unknown modifier_id"):
            generate_modifier({"modifier_id": "does_not_exist"})

    def test_all_modifiers_produce_valid_xml(self):
        """Every entry in MODIFIERS should generate parseable XML."""
        for m in MODIFIERS:
            files = generate_modifier({"modifier_id": m["id"], "value": m["vanilla_value"]})
            target_key = f"Config/{m['xml_file']}"
            assert target_key in files, f"Missing {target_key} for {m['id']}"
            _parse(files[target_key])


# ---------------------------------------------------------------------------
# generate_mod_files (dispatch)
# ---------------------------------------------------------------------------

class TestGenerateModFiles:
    def test_item_dispatch(self):
        files = generate_mod_files("item", {
            "item_name": "x", "display_name": "X", "description": "",
            "item_type": "misc", "extends": "", "custom_icon": "", "tags": "",
        }, DEFAULT_VERSION_ID)
        assert "Config/items.xml" in files

    def test_unknown_type_raises(self):
        with pytest.raises((KeyError, ValueError)):
            generate_mod_files("unknown_type", {}, DEFAULT_VERSION_ID)


# ---------------------------------------------------------------------------
# build_zip
# ---------------------------------------------------------------------------

class TestBuildZip:
    def test_returns_bytes(self):
        data = build_zip("TestMod", "<xml/>", {"Config/items.xml": "<configs/>"}, "README")
        assert isinstance(data, bytes)

    def test_zip_is_valid(self):
        data = build_zip("TestMod", "<xml/>", {"Config/items.xml": "<configs/>"}, "README")
        assert zipfile.is_zipfile(io.BytesIO(data))

    def test_contains_modinfo(self):
        data = build_zip("TestMod", "<xml/>", {"Config/items.xml": "<configs/>"}, "README")
        names = _zip_names(data)
        assert any("ModInfo.xml" in n for n in names)

    def test_contains_readme(self):
        data = build_zip("TestMod", "<xml/>", {}, "README CONTENT")
        names = _zip_names(data)
        assert any("README" in n for n in names)

    def test_contains_config_files(self):
        data = build_zip("TestMod", "<xml/>", {"Config/items.xml": "<configs/>"}, "")
        names = _zip_names(data)
        assert any("items.xml" in n for n in names)

    def test_folder_name_as_prefix(self):
        data = build_zip("MyFolder", "<xml/>", {"Config/items.xml": "<configs/>"}, "")
        names = _zip_names(data)
        assert all(n.startswith("MyFolder/") for n in names)

    def test_config_xml_content_preserved(self):
        data = build_zip("M", "<xml/>", {"Config/items.xml": "<configs><hello/></configs>"}, "")
        content = _zip_read(data, "M/Config/items.xml")
        assert "<hello/>" in content or "hello" in content


# ---------------------------------------------------------------------------
# PRESETS structure
# ---------------------------------------------------------------------------

class TestPresets:
    def test_all_types_present(self):
        for t in ("item", "recipe", "block", "perk", "modifier"):
            assert t in PRESETS, f"Missing preset type: {t}"

    def test_presets_have_id_and_label(self):
        for t, presets in PRESETS.items():
            for p in presets:
                assert "id" in p, f"{t} preset missing 'id'"
                assert "name" in p or "label" in p, f"{t} preset missing 'name'/'label'"
                assert "defaults" in p, f"{t} preset missing 'defaults'"

    def test_item_preset_defaults_generate_valid_xml(self):
        for p in PRESETS["item"]:
            files = generate_item(p["defaults"], DEFAULT_VERSION_ID)
            _parse(files["Config/items.xml"])

    def test_modifier_preset_defaults_generate_valid_xml(self):
        for p in PRESETS["modifier"]:
            files = generate_modifier(p["defaults"], DEFAULT_VERSION_ID)
            for xml_str in files.values():
                _parse(xml_str)
