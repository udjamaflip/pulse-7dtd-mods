"""SQLite storage for generated mods.

Schema stores form data, version snapshot, readme, and ZIP bytes so mods can
be re-downloaded and inspected without regeneration.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _migrate(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mods (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_name          TEXT NOT NULL,
                mod_type          TEXT NOT NULL,
                created_at        TEXT NOT NULL,
                form_data         TEXT NOT NULL,
                zip_data          BLOB NOT NULL,
                game_version      TEXT NOT NULL,
                game_version_label TEXT NOT NULL,
                version_notes     TEXT NOT NULL,
                readme_text       TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def save_mod(
        self,
        *,
        mod_name: str,
        mod_type: str,
        form_data: dict,
        zip_data: bytes,
        game_version: str,
        game_version_label: str,
        version_notes: str,
        readme_text: str,
    ) -> int:
        """Insert a new mod record and return its id."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.execute(
            """
            INSERT INTO mods
                (mod_name, mod_type, created_at, form_data, zip_data,
                 game_version, game_version_label, version_notes, readme_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mod_name,
                mod_type,
                now,
                json.dumps(form_data),
                zip_data,
                game_version,
                game_version_label,
                version_notes,
                readme_text,
            ),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def delete_mod(self, mod_id: int) -> bool:
        """Delete a mod by id. Returns True if a row was deleted."""
        cur = self.conn.execute("DELETE FROM mods WHERE id = ?", (mod_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_mod(self, mod_id: int) -> dict | None:
        """Return a single mod as a dict, or None if not found."""
        cur = self.conn.execute("SELECT * FROM mods WHERE id = ?", (mod_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def get_zip(self, mod_id: int) -> bytes | None:
        """Return only the ZIP bytes for a mod, or None if not found."""
        cur = self.conn.execute("SELECT zip_data FROM mods WHERE id = ?", (mod_id,))
        row = cur.fetchone()
        return bytes(row["zip_data"]) if row else None

    def list_mods(self, limit: int = 100) -> list[dict]:
        """Return recent mods without the ZIP blob (for listing pages)."""
        cur = self.conn.execute(
            """
            SELECT id, mod_name, mod_type, created_at,
                   game_version, game_version_label, version_notes, readme_text, form_data
            FROM mods
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_dict(row) for row in cur.fetchall()]

    def count_today(self) -> int:
        """Return the number of mods created today (for the shell badge)."""
        today = date.today().isoformat()
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM mods WHERE created_at >= ?",
            (today + " 00:00:00",),
        )
        return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        try:
            d["form_data"] = json.loads(d["form_data"])
        except Exception:
            d["form_data"] = {}
        # zip_data is intentionally kept as bytes/None; callers that don't need
        # it use list_mods() which excludes the column.
        if "zip_data" in d and d["zip_data"] is not None:
            d["zip_data"] = bytes(d["zip_data"])
        return d

    def close(self) -> None:
        self.conn.close()
