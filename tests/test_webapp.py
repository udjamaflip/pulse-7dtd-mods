"""Tests for src.webapp — FastAPI route smoke tests."""

import io
import json
import zipfile
import tempfile
import os

import pytest
from fastapi.testclient import TestClient

# Patch the data directory so tests use a temp location
_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATA_DIR", _tmp)
os.environ.setdefault("APP_PORT", "8003")
os.environ.setdefault("DEFAULT_GAME_VERSION", "v1")

from src.webapp import app  # noqa: E402  (import after env patch)


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------------------

class TestStaticPages:
    def test_home_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_howto_200(self, client):
        r = client.get("/howto")
        assert r.status_code == 200

    def test_create_200(self, client):
        r = client.get("/create")
        assert r.status_code == 200

    def test_create_item_form_200(self, client):
        r = client.get("/create/item")
        assert r.status_code == 200

    def test_create_recipe_form_200(self, client):
        r = client.get("/create/recipe")
        assert r.status_code == 200

    def test_create_block_form_200(self, client):
        r = client.get("/create/block")
        assert r.status_code == 200

    def test_create_perk_form_200(self, client):
        r = client.get("/create/perk")
        assert r.status_code == 200

    def test_create_modifier_form_200(self, client):
        r = client.get("/create/modifier")
        assert r.status_code == 200

    def test_create_form_with_preset(self, client):
        r = client.get("/create/item?preset=iron_sword&version=v1")
        assert r.status_code == 200

    def test_create_form_unknown_preset_still_200(self, client):
        r = client.get("/create/item?preset=nonexistent&version=v1")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

class TestApiNewItems:
    def test_returns_count(self, client):
        r = client.get("/api/new-items")
        assert r.status_code == 200
        body = r.json()
        assert "count" in body
        assert isinstance(body["count"], int)


# ---------------------------------------------------------------------------
# Create flow — item
# ---------------------------------------------------------------------------

class TestCreateItem:
    FORM_DATA = {
        "item_name": "test_IronSword",
        "display_name": "Iron Sword",
        "description": "A test sword.",
        "item_type": "melee_weapon",
        "extends": "",
        "custom_icon": "",
        "damage": "40",
        "range": "2.5",
        "attack_delay": "0.8",
        "durability": "300",
        "tags": "",
        "game_version": "v1",
    }

    def test_post_redirects(self, client):
        r = client.post("/create/item", data=self.FORM_DATA, follow_redirects=False)
        assert r.status_code in (302, 303)

    def test_post_creates_mod(self, client):
        r = client.post("/create/item", data=self.FORM_DATA, follow_redirects=True)
        assert r.status_code == 200
        # mod_name is the URL-safe display_name (spaces → underscores)
        assert "Iron" in r.text

    def test_mod_detail_page(self, client):
        r = client.post("/create/item", data=self.FORM_DATA, follow_redirects=True)
        # After redirect the mod_detail page should render README content
        assert r.status_code == 200
        assert "README" in r.text or "Install" in r.text


# ---------------------------------------------------------------------------
# Create flow — recipe
# ---------------------------------------------------------------------------

class TestCreateRecipe:
    FORM_DATA = {
        "recipe_output": "test_IronSword",
        "output_count": "1",
        "craft_area": "workbench",
        "craft_time": "15",
        "description": "Recipe for iron sword.",
        "ingredient_name_0": "resourceIronIngot",
        "ingredient_count_0": "10",
        "ingredient_name_1": "resourceWood",
        "ingredient_count_1": "5",
        "game_version": "v1",
    }

    def test_post_redirects(self, client):
        r = client.post("/create/recipe", data=self.FORM_DATA, follow_redirects=False)
        assert r.status_code in (302, 303)


# ---------------------------------------------------------------------------
# Create flow — modifier
# ---------------------------------------------------------------------------

class TestCreateModifier:
    def test_solar_post_redirects(self, client):
        data = {
            "modifier_id": "solar_power_boost",
            "value": "2.0",
            "display_name": "2x Solar",
            "description": "",
            "game_version": "v2_5",
        }
        r = client.post("/create/modifier", data=data, follow_redirects=False)
        assert r.status_code in (302, 303)

    def test_blocks_modifier_post_redirects(self, client):
        data = {
            "modifier_id": "forge_heat",
            "value": "0",
            "display_name": "Stealth Forge",
            "description": "",
            "game_version": "v2_5",
        }
        r = client.post("/create/modifier", data=data, follow_redirects=False)
        assert r.status_code in (302, 303)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

class TestDownload:
    def _create_item(self, client):
        data = {
            "item_name": "dl_TestItem",
            "display_name": "DL Test",
            "description": "",
            "item_type": "misc",
            "extends": "",
            "custom_icon": "",
            "tags": "",
            "game_version": "v1",
        }
        r = client.post("/create/item", data=data, follow_redirects=False)
        location = r.headers["location"]
        # extract id from /mod/{id}?created=1
        mod_id = int(location.split("/mod/")[1].split("?")[0])
        return mod_id

    def test_download_returns_zip(self, client):
        mod_id = self._create_item(client)
        r = client.get(f"/download/{mod_id}")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"

    def test_download_zip_is_valid(self, client):
        mod_id = self._create_item(client)
        r = client.get(f"/download/{mod_id}")
        assert zipfile.is_zipfile(io.BytesIO(r.content))

    def test_download_missing_404(self, client):
        r = client.get("/download/999999")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDelete:
    def _create_item(self, client):
        data = {
            "item_name": "del_TestItem",
            "display_name": "Del Test",
            "description": "",
            "item_type": "misc",
            "extends": "",
            "custom_icon": "",
            "tags": "",
            "game_version": "v1",
        }
        r = client.post("/create/item", data=data, follow_redirects=False)
        location = r.headers["location"]
        return int(location.split("/mod/")[1].split("?")[0])

    def test_delete_returns_ok(self, client):
        mod_id = self._create_item(client)
        r = client.delete(f"/mod/{mod_id}")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_delete_removes_mod(self, client):
        mod_id = self._create_item(client)
        client.delete(f"/mod/{mod_id}")
        r = client.get(f"/download/{mod_id}")
        assert r.status_code == 404

    def test_delete_missing_returns_404(self, client):
        r = client.delete("/mod/999999")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Build modpack
# ---------------------------------------------------------------------------

class TestBuildDownload:
    ITEMS = [
        {
            "modifier_id": "solar_power_boost",
            "label": "Solar Bank Power Multiplier",
            "category": "Power",
            "value": "2.0",
            "vanilla_value": "1.0",
            "property_name": "PowerOutputMultiplier",
            "target_name": "solarBank",
            "xml_file": "items.xml",
            "display_name": "Double Solar",
            "description": "",
        },
        {
            "modifier_id": "forge_heat",
            "label": "Forge Heat Map Strength",
            "category": "Workstations",
            "value": "0",
            "vanilla_value": "6",
            "property_name": "HeatMapStrength",
            "target_name": "forge",
            "xml_file": "blocks.xml",
            "display_name": "Stealth Forge",
            "description": "",
        },
    ]

    def test_build_returns_zip(self, client):
        r = client.post("/build/download", json={"items": self.ITEMS, "pack_name": "TestPack"})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"

    def test_build_zip_contains_both_mods(self, client):
        r = client.post("/build/download", json={"items": self.ITEMS, "pack_name": "TestPack"})
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        names = zf.namelist()
        # Each mod has at least a ModInfo.xml
        assert any("Double_Solar" in n for n in names)
        assert any("Stealth_Forge" in n for n in names)

    def test_build_empty_items_returns_400(self, client):
        r = client.post("/build/download", json={"items": [], "pack_name": "TestPack"})
        assert r.status_code == 400

    def test_build_invalid_modifier_returns_400(self, client):
        bad_item = dict(self.ITEMS[0])
        bad_item["modifier_id"] = "nonexistent_mod"
        r = client.post("/build/download", json={"items": [bad_item], "pack_name": "TestPack"})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Embedded mode
# ---------------------------------------------------------------------------

class TestEmbedded:
    def test_home_embedded_200(self, client):
        r = client.get("/?embedded=1")
        assert r.status_code == 200

    def test_howto_embedded_200(self, client):
        r = client.get("/howto?embedded=1")
        assert r.status_code == 200
