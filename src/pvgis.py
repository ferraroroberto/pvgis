"""
PVGIS API client
================
Thin wrapper over the JRC PVGIS **non-interactive** REST service (the
``PVcalc`` endpoint): estimate the energy output of a grid-connected PV
system for any location. The service is free and needs no API key, and
returns exactly the same numbers as the interactive web tool.

Docs: https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/getting-started-pvgis/api-non-interactive-service_en
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests

from src import get_logger
from src.config import PVGIS_API_BASE

log = get_logger("pvgis")

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


@dataclass
class MonthEstimate:
    """One month of the yearly profile."""

    month: int  # 1-12
    energy_kwh: float  # E_m — average monthly energy production
    irradiation_kwh_m2: float  # H(i)_m — in-plane irradiation

    @property
    def name(self) -> str:
        return MONTH_NAMES[self.month - 1]


@dataclass
class PVEstimate:
    """Parsed result of a ``PVcalc`` call for a fixed-mounted system."""

    yearly_energy_kwh: float  # E_y
    monthly_avg_kwh: float  # E_m (averaged over the year)
    daily_avg_kwh: float  # E_d
    yearly_irradiation_kwh_m2: float  # H(i)_y
    total_loss_pct: float  # l_total
    elevation_m: float
    monthly: list[MonthEstimate] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def estimate(
    *,
    lat: float,
    lon: float,
    peakpower: float,
    loss: float = 14.0,
    angle: float = 35.0,
    aspect: float = 0.0,
    mountingplace: str = "building",
    pvtech: str = "crystSi",
    timeout: float = 30.0,
) -> PVEstimate:
    """Estimate yearly + monthly PV output for one location.

    Args:
        lat, lon: Site coordinates in decimal degrees.
        peakpower: System nominal (peak) power in kW.
        loss: Combined system losses as a percentage (PVGIS default 14).
        angle: Tilt from horizontal, in degrees (0 = flat).
        aspect: Azimuth in degrees — 0 = south, -90 = east, 90 = west.
        mountingplace: ``"building"`` (roof) or ``"free"`` (free-standing).
        pvtech: Module technology — ``"crystSi"``, ``"CIS"``, ``"CdTe"`` or ``"Unknown"``.
        timeout: HTTP timeout in seconds.

    Returns:
        A :class:`PVEstimate` with totals and the 12-month profile.

    Raises:
        requests.HTTPError: on a non-2xx response (e.g. coordinates outside
            the PVGIS coverage area).
    """
    params = {
        "lat": lat,
        "lon": lon,
        "peakpower": peakpower,
        "loss": loss,
        "angle": angle,
        "aspect": aspect,
        "mountingplace": mountingplace,
        "pvtechchoice": pvtech,
        "outputformat": "json",
    }
    log.info(
        "PVcalc request: lat=%.4f lon=%.4f peak=%skW tilt=%s° azimuth=%s°",
        lat, lon, peakpower, angle, aspect,
    )

    resp = requests.get(f"{PVGIS_API_BASE}/PVcalc", params=params, timeout=timeout)
    if not resp.ok:
        # PVGIS puts a human-readable reason in the body for bad inputs.
        log.error("PVcalc failed (%s): %s", resp.status_code, resp.text[:200])
    resp.raise_for_status()
    data = resp.json()

    totals = data["outputs"]["totals"]["fixed"]
    monthly_raw = data["outputs"]["monthly"]["fixed"]
    location = data["inputs"]["location"]

    result = PVEstimate(
        yearly_energy_kwh=float(totals["E_y"]),
        monthly_avg_kwh=float(totals["E_m"]),
        daily_avg_kwh=float(totals["E_d"]),
        yearly_irradiation_kwh_m2=float(totals["H(i)_y"]),
        total_loss_pct=float(totals["l_total"]),
        elevation_m=float(location.get("elevation", 0.0)),
        monthly=[
            MonthEstimate(
                month=int(m["month"]),
                energy_kwh=float(m["E_m"]),
                irradiation_kwh_m2=float(m["H(i)_m"]),
            )
            for m in monthly_raw
        ],
        raw=data,
    )
    log.info(
        "PVcalc result: %.0f kWh/year (elevation %.0f m)",
        result.yearly_energy_kwh, result.elevation_m,
    )
    return result
