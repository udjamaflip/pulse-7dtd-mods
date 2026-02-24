"""7 Days to Die Mod Maker — FastAPI web application.

Standalone: no imports from parent Pulse shell. Supports ?embedded=1 to
suppress the in-app navigation when running inside the Pulse iframe shell.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv

load_dotenv()

from .config_store import ConfigStore
from .generator import (
    MODIFIERS,
    PRESETS,
    build_zip,
    generate_mod_files,
    make_modinfo_xml,
    make_readme_txt,
)
from .storage import Storage
from .versions import SUPPORTED_VERSIONS, get_version

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="7 Days to Die Mod Maker")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

config_store = ConfigStore()
config = config_store.ensure()
storage = Storage(config.database_path)

# Human-readable labels for mod types
MOD_TYPE_LABELS: dict[str, str] = {
    "item": "Item",
    "recipe": "Recipe",
    "block": "Block",
    "perk": "Perk / Progression",
    "modifier": "Modifier",
}

MODIFIER_TYPE_LABELS: dict[str, str] = {
    "solar_power": "Solar Power Boost",
    "zombie_hp": "Zombie HP Multiplier",
    "loot_multiplier": "Loot Multiplier",
    "recipe_cost": "Recipe Cost",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _safe_folder_name(name: str) -> str:
    """Convert a display name to a safe mod folder name."""
    safe = re.sub(r"[^\w\-]", "_", name.strip())
    return safe or "MyMod"


def _embedded(request: Request) -> bool:
    return request.query_params.get("embedded", "0") == "1"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    mods = storage.list_mods()
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "mods": mods,
            "mod_type_labels": MOD_TYPE_LABELS,
            "active_page": "home",
            "embedded": _embedded(request),
        },
    )


@app.get("/howto", response_class=HTMLResponse)
async def howto(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "howto.html",
        {
            "request": request,
            "versions": SUPPORTED_VERSIONS,
            "active_page": "howto",
            "embedded": _embedded(request),
        },
    )


@app.get("/create", response_class=HTMLResponse)
async def create_picker(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "presets": PRESETS,
            "mod_types": MOD_TYPE_LABELS,
            "versions": SUPPORTED_VERSIONS,
            "default_version": config.default_game_version,
            "active_page": "create",
            "embedded": _embedded(request),
        },
    )


@app.get("/create/{mod_type}", response_class=HTMLResponse)
async def create_form(request: Request, mod_type: str) -> HTMLResponse:
    if mod_type not in MOD_TYPE_LABELS:
        return HTMLResponse(f"Unknown mod type: {mod_type}", status_code=404)

    preset_id = request.query_params.get("preset", "")
    version_id = request.query_params.get("version", config.default_game_version)

    # Pre-fill defaults from preset if one is requested
    preset_defaults: dict[str, Any] = {}
    preset_desc = ""
    for p in PRESETS.get(mod_type, []):
        if p["id"] == preset_id:
            preset_defaults = p["defaults"]
            preset_desc = p["description"]
            break

    template_name = f"form_{mod_type}.html"
    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "mod_type": mod_type,
            "mod_type_label": MOD_TYPE_LABELS[mod_type],
            "presets": PRESETS.get(mod_type, []),
            "preset_id": preset_id,
            "preset_desc": preset_desc,
            "defaults": preset_defaults,
            "versions": SUPPORTED_VERSIONS,
            "version_id": version_id,
            "version": get_version(version_id),
            "modifier_type_labels": MODIFIER_TYPE_LABELS,
            "modifiers_json": json.dumps(MODIFIERS),
            "active_page": "create",
            "embedded": _embedded(request),
        },
    )


@app.post("/create/{mod_type}")
async def create_mod(request: Request, mod_type: str) -> Response:
    if mod_type not in MOD_TYPE_LABELS:
        return HTMLResponse(f"Unknown mod type: {mod_type}", status_code=404)

    form = await request.form()
    form_data: dict[str, Any] = dict(form)

    version_id = form_data.pop("game_version", config.default_game_version)
    version_def = get_version(version_id)

    # Parse dynamic ingredient rows (recipe form sends ingredient_name_0, ingredient_count_0, ...)
    if mod_type == "recipe":
        ingredients: list[dict[str, str]] = []
        i = 0
        while True:
            name_key = f"ingredient_name_{i}"
            count_key = f"ingredient_count_{i}"
            if name_key not in form_data:
                break
            ing_name = str(form_data.pop(name_key, "")).strip()
            ing_count = str(form_data.pop(count_key, "1")).strip()
            if ing_name:
                ingredients.append({"name": ing_name, "count": ing_count})
            i += 1
        form_data["ingredients"] = ingredients

    # Derive mod folder name from display_name or item_name / block_name / perk_name
    raw_name = (
        form_data.get("display_name")
        or form_data.get("item_name")
        or form_data.get("block_name")
        or form_data.get("perk_name")
        or form_data.get("recipe_output")
        or "MyMod"
    )
    mod_folder = _safe_folder_name(str(raw_name))
    mod_display = str(form_data.get("display_name") or raw_name)
    description = str(form_data.get("description") or "")

    # Generate config XML files
    config_files = generate_mod_files(mod_type, form_data, version_id)

    # Generate ModInfo.xml
    mod_info = make_modinfo_xml(
        name=mod_folder,
        display_name=mod_display,
        description=description,
    )

    # Generate README.txt (snapshot)
    readme = make_readme_txt(
        mod_name=mod_folder,
        mod_type=mod_type,
        form_data=form_data,
        version_def=version_def,
    )

    # Build ZIP
    zip_bytes = build_zip(mod_folder, mod_info, config_files, readme)

    # Save to DB (snapshot version info and readme)
    mod_id = storage.save_mod(
        mod_name=mod_folder,
        mod_type=mod_type,
        form_data=form_data,
        zip_data=zip_bytes,
        game_version=version_id,
        game_version_label=version_def["label"],
        version_notes=version_def["notes"],
        readme_text=readme,
    )

    log.info("Generated mod %r (type=%s, version=%s, id=%s)", mod_folder, mod_type, version_id, mod_id)
    return RedirectResponse(url=f"/mod/{mod_id}?created=1", status_code=303)


@app.get("/mod/{mod_id}", response_class=HTMLResponse)
async def mod_detail(request: Request, mod_id: int) -> HTMLResponse:
    mod = storage.get_mod(mod_id)
    if mod is None:
        return HTMLResponse("Mod not found", status_code=404)
    # Exclude binary ZIP data from template context
    mod_display = {k: v for k, v in mod.items() if k != "zip_data"}
    return templates.TemplateResponse(
        "mod_detail.html",
        {
            "request": request,
            "mod": mod_display,
            "mod_type_labels": MOD_TYPE_LABELS,
            "modifier_type_labels": MODIFIER_TYPE_LABELS,
            "created": request.query_params.get("created") == "1",
            "active_page": "home",
            "embedded": _embedded(request),
        },
    )


@app.get("/download/{mod_id}")
async def download_mod(mod_id: int) -> Response:
    zip_bytes = storage.get_zip(mod_id)
    if zip_bytes is None:
        return HTMLResponse("Mod not found", status_code=404)

    mod = storage.get_mod(mod_id)
    filename = f"{mod['mod_name']}.zip" if mod else f"mod_{mod_id}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/mod/{mod_id}")
async def delete_mod(mod_id: int) -> JSONResponse:
    deleted = storage.delete_mod(mod_id)
    if not deleted:
        return JSONResponse({"ok": False, "error": "Not found"}, status_code=404)
    return JSONResponse({"ok": True})


@app.get("/api/new-items")
async def api_new_items() -> JSONResponse:
    """Return count of mods created today. Used by the Pulse shell for badge counts."""
    try:
        return JSONResponse({"count": storage.count_today()})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"count": 0, "error": str(exc)})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    cfg = config_store.ensure()
    uvicorn.run("src.webapp:app", host="0.0.0.0", port=cfg.app_port, reload=False)
