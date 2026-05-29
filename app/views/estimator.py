"""
PV Estimator view
=================
Enter a roof's location and PV-system parameters, call the PVGIS API,
and show the estimated yearly + monthly energy production.
"""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from src import get_logger
from src.config import (
    HOME_AZIMUTH_DEG,
    HOME_LAT,
    HOME_LON,
    HOME_LOSS_PCT,
    HOME_PEAKPOWER_KW,
    HOME_TILT_DEG,
)
from src.pvgis import estimate

log = get_logger("ui.estimator")

_PVTECH = {
    "Crystalline silicon": "crystSi",
    "CIS": "CIS",
    "Cadmium telluride (CdTe)": "CdTe",
}


def render() -> None:
    st.header("☀ PV Estimator")
    st.caption(
        "Estimates grid-connected PV output via the EU JRC **PVGIS** "
        "non-interactive API (free, no key). Same numbers as the web tool."
    )

    with st.form("pv_form"):
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(
                "Latitude", value=HOME_LAT, min_value=-90.0, max_value=90.0,
                format="%.4f", key="lat",
            )
            lon = st.number_input(
                "Longitude", value=HOME_LON, min_value=-180.0, max_value=180.0,
                format="%.4f", key="lon",
            )
            peakpower = st.number_input(
                "Peak power (kWp)", value=HOME_PEAKPOWER_KW, min_value=0.1,
                step=0.5, format="%.2f", key="peakpower",
            )
        with c2:
            tilt = st.slider(
                "Tilt from horizontal (°)", 0, 90, int(HOME_TILT_DEG), key="tilt",
            )
            azimuth = st.slider(
                "Azimuth (° — 0 = south, −90 = east, 90 = west)",
                -180, 180, int(HOME_AZIMUTH_DEG), key="azimuth",
            )
            loss = st.slider(
                "System losses (%)", 0, 30, int(HOME_LOSS_PCT), key="loss",
            )

        c3, c4 = st.columns(2)
        with c3:
            tech_label = st.selectbox(
                "Module technology", list(_PVTECH), key="pvtech",
            )
        with c4:
            mounting = st.radio(
                "Mounting", ["building", "free"], horizontal=True, key="mounting",
            )

        submitted = st.form_submit_button("Estimate", type="primary")

    if not submitted:
        return

    try:
        with st.spinner("Querying PVGIS…"):
            result = estimate(
                lat=lat,
                lon=lon,
                peakpower=peakpower,
                loss=float(loss),
                angle=float(tilt),
                aspect=float(azimuth),
                mountingplace=mounting,
                pvtech=_PVTECH[tech_label],
            )
    except requests.HTTPError as exc:
        log.warning("PVGIS rejected the request: %s", exc)
        st.error(
            "PVGIS could not process that request. Check the coordinates are "
            "inside its coverage area (Europe, Africa, most of Asia/Americas)."
        )
        return
    except requests.RequestException as exc:
        log.error("PVGIS request failed: %s", exc)
        st.error(f"Could not reach PVGIS: {exc}")
        return

    st.success(f"Estimated **{result.yearly_energy_kwh:,.0f} kWh/year**")

    m1, m2, m3 = st.columns(3)
    m1.metric("Yearly energy", f"{result.yearly_energy_kwh:,.0f} kWh")
    m2.metric("Daily average", f"{result.daily_avg_kwh:,.1f} kWh")
    m3.metric("Elevation", f"{result.elevation_m:,.0f} m")

    df = pd.DataFrame(
        {
            "Month": [m.name for m in result.monthly],
            "Energy (kWh)": [m.energy_kwh for m in result.monthly],
            "Irradiation (kWh/m²)": [m.irradiation_kwh_m2 for m in result.monthly],
        }
    ).set_index("Month")

    st.subheader("Monthly energy production")
    st.bar_chart(df["Energy (kWh)"], width="stretch")

    with st.expander("Monthly detail & system losses"):
        st.caption(f"Total system losses applied: {result.total_loss_pct:.1f}%")
        st.dataframe(df, width="stretch")
