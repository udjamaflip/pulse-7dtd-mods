# 7 Days to Die Mod Maker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A web UI for generating **7 Days to Die XML modlets**. Fill in a form, pick your game version, and download a ready-to-install ZIP — complete with `ModInfo.xml`, config XMLs, and a plain-text `README.txt` with install instructions baked in.

---

## Features

- **Mod types supported:** Items, Recipes, Blocks, Progression/Perks, Modifiers (solar power output, zombie HP, loot chance, recipe costs)
- **Starter templates/presets** per type to pre-fill forms
- **Version targeting** — generates XML appropriate for A21 or V1.x, with known compatibility notes
- **ZIP download** — ready to drop straight into your `Mods/` folder
- **Mod history** — saved to SQLite; re-download or review any previously generated mod
- **README.txt bundled in every ZIP** — contains mod description, target version, compatibility notes, and step-by-step install instructions
- **How To page** — install guide covering platform paths, folder structure, and troubleshooting
- **Pulse shell integration** — runs as an iframe applet in the [Pulse](https://github.com/udjamaflip/pulse) dashboard

---

## Quickstart (local)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python -m src.webapp
```

Open http://localhost:8003

---

## Quickstart (Docker)

```bash
docker build -t 7dtd-modmaker .
docker run -d \
  -p 8003:8003 \
  -v "$(pwd)/data:/app/data" \
  7dtd-modmaker
```

---

## Pulse Shell Integration

Add to `manifest.json` in the [Pulse](https://github.com/udjamaflip/pulse) repo:

```json
{
  "slug": "7dtd-modmaker",
  "nav_label": "7DtD Mods",
  "icon": "wrench",
  "nav_order": 3,
  "type": "iframe",
  "port": 8003
}
```

Add to `docker-compose.yml`:

```yaml
7dtd-modmaker:
  build:
    context: applets/7dtd-modmaker
    dockerfile: Dockerfile
  container_name: pulse-7dtd-modmaker
  environment:
    - APP_PORT=8003
  ports:
    - "8003:8003"
  volumes:
    - "${DATA_DIR:-./data}:/app/data"
  restart: unless-stopped
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `8003` | Port the web UI listens on |
| `DATA_DIR` | `./data` | Directory for SQLite database and config |
| `DEFAULT_GAME_VERSION` | `v1` | Default version pre-selected on forms (`a21`, `v1`, `exp`) |

Copy `.env.example` to `.env` and edit as needed.

---

## Supported Game Versions

| ID | Label | Notes |
|---|---|---|
| `a21` | Alpha 21 (Stable) | XPath modding supported; `progression.xml` renamed; `loot.xml` restructured |
| `v1` | V1.0+ (1.x Stable) | Default. Biome loot split into separate files; `progression.xml` uses updated format |
| `exp` | Experimental | May differ from V1.x — use at own risk |

Version details and caveats are shown on the form and bundled into the ZIP's `README.txt`.

---

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Disclaimer

This project is not affiliated with The Fun Pimps or 7 Days to Die. All game content references are for interoperability purposes only.

---

## License

MIT — see [LICENSE](LICENSE).
