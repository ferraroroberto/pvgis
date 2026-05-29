# PVGIS House Estimator

Estimate the solar-PV output of a house using the EU Joint Research Centre's **[PVGIS](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en)** service. A small Streamlit app that calls the PVGIS *non-interactive* REST API (`PVcalc`) — **free, no API key** — and shows estimated yearly and monthly energy production for a given roof.

> **Why an API client and not a fork of [`code.europa.eu/pvgis/pvgis`](https://code.europa.eu/pvgis/pvgis)?** That repository is the full PVGIS *server system*; running it means hosting the service plus its terabyte-scale solar-radiation databases (SARAH / ERA5). For estimating one house that is wildly out of proportion. The public non-interactive API returns the exact same numbers as the web tool, so this project just calls it.

## What it does

- **`app/`** — Streamlit UI: a `PV Estimator` view (location + system form → yearly/monthly charts) and a welcome page.
- **`src/pvgis.py`** — typed client for the PVGIS `PVcalc` endpoint; parses totals and the 12-month profile into dataclasses.
- **`src/config.py`** — env-driven settings loaded from `.env`; your house's coordinates live there and stay out of git.
- An **elegant logger** (`src/logger.py`) writing to terminal (color-coded), a rotating file at `data/logs/app.log`, and a live panel in the UI — all from one `log.info(...)`.
- Dark theme by default (`app/.streamlit/config.toml`) + a runtime light-mode toggle.
- `launch_app.{bat,sh}` (local) and `launch_server.{bat,sh}` (local + Cloudflare Tunnel for sharing).

## Setup

```powershell
cd E:\automation\pvgis
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # then edit .env with your house's details
```

POSIX: `python3 -m venv .venv && ./.venv/bin/python -m pip install -r requirements.txt && cp .env.example .env`.

**Never activate the venv** — invoke it directly (`& .\.venv\Scripts\python.exe ...` on Windows, `./.venv/bin/python ...` on POSIX), per `CLAUDE.md`.

### Configure your house

The estimator form is pre-filled from `.env` (gitignored). Copy `.env.example` → `.env` and set:

| Key | Meaning |
| --- | --- |
| `HOME_LAT` / `HOME_LON` | Roof coordinates (decimal degrees) |
| `HOME_PEAKPOWER_KW` | System peak power, kWp |
| `HOME_LOSS_PCT` | Combined system losses (PVGIS default 14) |
| `HOME_TILT_DEG` | Panel tilt from horizontal (0 = flat) |
| `HOME_AZIMUTH_DEG` | Orientation: 0 = south, −90 = east, 90 = west |

This repo is **public** — `.env` is gitignored precisely so your location is never committed. Everything else is shared for learning.

## Run

```powershell
launch_app.bat                                   # Windows, opens browser
./launch_app.sh                                  # macOS / Linux
& .\.venv\Scripts\python.exe -m streamlit run app/app.py   # direct
```

Then open the **☀ PV Estimator** view in the sidebar.

## Layout

```
app/
  .streamlit/config.toml    default (dark) theme + server defaults
  styles/light.css          light-mode overlay (runtime-injected)
  app.py                    Streamlit entry: page config, st.navigation, light/dark toggle
  views/                    one render() per file (welcome, estimator)
src/
  config.py                 paths + .env-driven settings (incl. HOME_* defaults)
  pvgis.py                  PVGIS PVcalc API client
  logger.py                 the elegant logger
  pipelines/                extension point for batch/CLI runs (one run() per file)
data/                       input / output / logs (gitignored)
launch_app.{bat,sh}
launch_server.{bat,sh}
```

## Conventions

- `app/app.py` prepends the project root to `sys.path`, so `from src.X import Y` works downstream. UI code in `app/` imports from `src/`, **never the reverse**.
- Views are `app/views/<name>.py`, each exporting `def render() -> None`; register by appending an `st.Page` entry to `nav_pages` in `app/app.py`. The directory is `views/` (not `pages/`) so Streamlit's auto-discovery doesn't duplicate the sidebar.
- Business logic lives in `src/` so it is reusable from the CLI and tests. Read settings from `src/config.py`, not `os.environ` directly.
- Logger usage:

  ```python
  from src import get_logger
  log = get_logger("pvgis")
  log.info("PVcalc request: lat=%.4f lon=%.4f", lat, lon)
  ```

  One call → terminal + rotating `data/logs/app.log` + in-memory ring buffer for live UI panels. Don't `print()`.

## Testing

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m playwright install chromium   # one-time, for e2e
```

```powershell
& .\.venv\Scripts\python.exe -m pytest                       # everything
& .\.venv\Scripts\python.exe -m pytest --ignore=tests/e2e     # unit only, fast
& .\.venv\Scripts\python.exe -m pytest tests/e2e              # e2e only
```

- **Unit** (`tests/test_*.py`) — hermetic. `test_pvgis.py` stubs the HTTP call against a fixture mirroring the real `PVcalc` JSON, so it runs offline.
- **Headless e2e** (`tests/e2e/`) — `pytest-playwright`. The `streamlit_app` fixture force-restarts Streamlit against the code on disk (`tests/_streamlit_lifecycle.py`), so it can never pass against a stale process. Expand per the regression-suite rules in `CLAUDE.md`. The e2e port is `STREAMLIT_E2E_PORT` in `tests/_streamlit_lifecycle.py`.

Force-restart the dev Streamlit yourself (handy when an edit isn't showing up):

```powershell
& .\.venv\Scripts\python.exe -c "from tests._streamlit_lifecycle import ensure_fresh_streamlit; ensure_fresh_streamlit()"
```

## Theming

Dark is the default (`app/.streamlit/config.toml`, Streamlit's native mechanism — read once at startup, propagates to every component). Light is a runtime CSS overlay (`app/styles/light.css`) injected on demand by the sidebar toggle, because `config.toml` can't be switched at runtime. To make light the default instead, swap them: put the light palette in `config.toml` and write a `dark.css` overlay. Overlay selectors target Streamlit `data-testid` / BaseWeb `data-baseweb` attributes — stable in practice, re-check after major Streamlit upgrades.

## Credits

Solar estimates by the **EU Joint Research Centre — PVGIS** ([re.jrc.ec.europa.eu](https://re.jrc.ec.europa.eu/pvg_tools/en/tools.html)). This project only queries their public API; all radiation modelling is theirs. Scaffolded from [`project-scaffolding`](https://github.com/ferraroroberto/project-scaffolding).
