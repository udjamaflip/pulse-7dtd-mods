# 7 Days to Die Mod Maker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A web UI for generating **7 Days to Die XML modlets**. Fill in a form and download a ready-to-install ZIP  complete with `ModInfo.xml`, config XMLs, and a `README.txt` with install instructions baked in.

Targets **7 Days to Die v2.5 (b32)**.

---

## Features

- **Mod types:** Items, Recipes, Blocks, Progression/Perks, Modifiers
- **27 real game modifiers** across 4 categories  Power, Turrets & Traps, Workstations, Economy  with searchable card UI, vanilla defaults, and value hints
- **ZIP download**  ready to drop straight into your `Mods/` folder
- **Mod history**  saved to SQLite; re-download or delete any previously generated mod
- **README.txt bundled in every ZIP**  mod description, target version, and step-by-step install instructions
- **How To page**  install guide covering platform paths, folder structure, and troubleshooting
- **Pulse shell integration**  runs as an iframe applet in the [Pulse](https://github.com/udjamaflip/pulse) dashboard

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
| `DATA_DIR` | `./data` | Directory for SQLite database |

---

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## Disclaimer

This project is not affiliated with The Fun Pimps or 7 Days to Die. All game content references are for interoperability purposes only.

---

## License

MIT  see [LICENSE](LICENSE).
