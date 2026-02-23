"""Tests for src.storage — SQLite CRUD operations."""

import json
import tempfile
import os

import pytest

from src.storage import Storage


@pytest.fixture
def db(tmp_path):
    """Fresh in-memory-backed Storage for each test."""
    path = str(tmp_path / "test.db")
    s = Storage(path)
    yield s


def _sample_mod(**overrides):
    base = dict(
        mod_name="TestMod",
        mod_type="item",
        form_data={"item_name": "test", "item_type": "misc"},
        zip_data=b"FAKEPK",
        game_version="v1",
        game_version_label="V1.0+ Stable",
        version_notes="No known issues.",
        readme_text="Install into Mods/.",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# save_mod / get_mod
# ---------------------------------------------------------------------------

class TestSaveMod:
    def test_returns_int_id(self, db):
        mid = db.save_mod(**_sample_mod())
        assert isinstance(mid, int)
        assert mid > 0

    def test_ids_are_sequential(self, db):
        id1 = db.save_mod(**_sample_mod())
        id2 = db.save_mod(**_sample_mod(mod_name="Another"))
        assert id2 > id1


class TestGetMod:
    def test_retrieves_saved_mod(self, db):
        mid = db.save_mod(**_sample_mod())
        row = db.get_mod(mid)
        assert row is not None
        assert row["mod_name"] == "TestMod"

    def test_returns_none_for_missing_id(self, db):
        assert db.get_mod(9999) is None

    def test_form_data_is_deserialized(self, db):
        mid = db.save_mod(**_sample_mod())
        row = db.get_mod(mid)
        assert isinstance(row["form_data"], dict)

    def test_zip_data_is_bytes(self, db):
        mid = db.save_mod(**_sample_mod())
        row = db.get_mod(mid)
        assert isinstance(row["zip_data"], bytes)
        assert row["zip_data"] == b"FAKEPK"

    def test_version_fields_stored(self, db):
        mid = db.save_mod(**_sample_mod())
        row = db.get_mod(mid)
        assert row["game_version"] == "v1"
        assert row["game_version_label"] == "V1.0+ Stable"
        assert row["version_notes"] == "No known issues."
        assert row["readme_text"] == "Install into Mods/."


# ---------------------------------------------------------------------------
# get_zip
# ---------------------------------------------------------------------------

class TestGetZip:
    def test_returns_bytes(self, db):
        mid = db.save_mod(**_sample_mod())
        data = db.get_zip(mid)
        assert data == b"FAKEPK"

    def test_returns_none_for_missing(self, db):
        assert db.get_zip(9999) is None


# ---------------------------------------------------------------------------
# delete_mod
# ---------------------------------------------------------------------------

class TestDeleteMod:
    def test_delete_removes_record(self, db):
        mid = db.save_mod(**_sample_mod())
        assert db.delete_mod(mid) is True
        assert db.get_mod(mid) is None

    def test_delete_missing_returns_false(self, db):
        assert db.delete_mod(9999) is False

    def test_delete_only_target(self, db):
        id1 = db.save_mod(**_sample_mod(mod_name="Mod1"))
        id2 = db.save_mod(**_sample_mod(mod_name="Mod2"))
        db.delete_mod(id1)
        assert db.get_mod(id2) is not None


# ---------------------------------------------------------------------------
# list_mods
# ---------------------------------------------------------------------------

class TestListMods:
    def test_returns_list(self, db):
        db.save_mod(**_sample_mod())
        rows = db.list_mods()
        assert isinstance(rows, list)
        assert len(rows) >= 1

    def test_empty_db_returns_empty_list(self, db):
        assert db.list_mods() == []

    def test_excludes_zip_data(self, db):
        db.save_mod(**_sample_mod())
        rows = db.list_mods()
        for row in rows:
            assert "zip_data" not in row or row.get("zip_data") is None

    def test_order_is_consistent(self, db):
        """list_mods returns rows in a consistent order (either ascending or descending id)."""
        id1 = db.save_mod(**_sample_mod(mod_name="First"))
        id2 = db.save_mod(**_sample_mod(mod_name="Second"))
        rows = db.list_mods()
        ids = [r["id"] for r in rows]
        assert ids == sorted(ids) or ids == sorted(ids, reverse=True)

    def test_limit_respected(self, db):
        for i in range(5):
            db.save_mod(**_sample_mod(mod_name=f"Mod{i}"))
        rows = db.list_mods(limit=3)
        assert len(rows) == 3


# ---------------------------------------------------------------------------
# count_today
# ---------------------------------------------------------------------------

class TestCountToday:
    def test_zero_initially(self, db):
        assert db.count_today() == 0

    def test_increments_on_save(self, db):
        db.save_mod(**_sample_mod())
        assert db.count_today() == 1

    def test_counts_multiple(self, db):
        db.save_mod(**_sample_mod())
        db.save_mod(**_sample_mod(mod_name="B"))
        assert db.count_today() == 2
