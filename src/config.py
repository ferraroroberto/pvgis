"""
Project configuration
=====================
Single place to read environment-driven settings.  Pipelines and pages
should import from here rather than reading ``os.environ`` directly so
defaults stay consistent.

Values are loaded from a local ``.env`` file (gitignored) if present, so
your own house's coordinates and system size never get committed.  See
``.env.example`` for the available keys.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOG_DIR = DATA_DIR / "logs"

# Load .env from the repo root before reading any settings below.
load_dotenv(ROOT_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "PVGIS House Estimator")
DEBUG = os.getenv("DEBUG", "0") == "1"

# PVGIS non-interactive API (free, no key). Override only to pin a version.
PVGIS_API_BASE = os.getenv("PVGIS_API_BASE", "https://re.jrc.ec.europa.eu/api/v5_3")


def _env_float(name: str, default: float) -> float:
    """Read a float env var, falling back to ``default`` if unset/blank/bad."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# Defaults that pre-fill the estimator form — put your own house here in .env.
HOME_LAT = _env_float("HOME_LAT", 40.4168)
HOME_LON = _env_float("HOME_LON", -3.7038)
HOME_PEAKPOWER_KW = _env_float("HOME_PEAKPOWER_KW", 4.0)
HOME_LOSS_PCT = _env_float("HOME_LOSS_PCT", 14.0)
HOME_TILT_DEG = _env_float("HOME_TILT_DEG", 35.0)
HOME_AZIMUTH_DEG = _env_float("HOME_AZIMUTH_DEG", 0.0)
