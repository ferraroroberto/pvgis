"""
PV Estimator view
=================
Enter a roof's location and PV-system parameters, call the PVGIS API,
and show the estimated yearly + monthly energy production.
"""

from __future__ import annotations

import altair as alt
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
                help="Roof latitude in decimal degrees (north positive). "
                "In Google Maps, right-click the spot → click the coordinates "
                "to copy them; latitude is the first number.",
            )
            lon = st.number_input(
                "Longitude", value=HOME_LON, min_value=-180.0, max_value=180.0,
                format="%.4f", key="lon",
                help="Roof longitude in decimal degrees (east positive, west "
                "negative). It is the second number in Google Maps coordinates.",
            )
            peakpower = st.number_input(
                "Peak power (kWp)", value=HOME_PEAKPOWER_KW, min_value=0.1,
                step=0.5, format="%.2f", key="peakpower",
                help="Total nominal (peak) power of all panels, in "
                "kilowatts-peak. Add up each panel's rated watts and divide by "
                "1000 — e.g. 16 panels × 500 W = 8 kWp.",
            )
        with c2:
            tilt = st.slider(
                "Tilt from horizontal (°)", 0, 90, int(HOME_TILT_DEG), key="tilt",
                help="Angle of the panels measured from flat ground. 0° = lying "
                "flat, 90° = vertical. Most pitched residential roofs are 25–40°.",
            )
            azimuth = st.slider(
                "Azimuth (° — 0 = south, −90 = east, 90 = west)",
                -180, 180, int(HOME_AZIMUTH_DEG), key="azimuth",
                help="Compass direction the panels face. 0° = due south (best in "
                "the northern hemisphere), −90° = east, +90° = west, ±180° = north.",
            )
            loss = st.slider(
                "System losses (%)", 0, 30, int(HOME_LOSS_PCT), key="loss",
                help="Combined real-world losses: cabling, inverter, dust, "
                "shading, temperature and ageing. PVGIS's default of 14% is a "
                "reasonable all-round estimate if you don't have a measured value.",
            )

        c3, c4 = st.columns(2)
        with c3:
            tech_label = st.selectbox(
                "Module technology", list(_PVTECH), key="pvtech",
                help="PV cell chemistry. 'Crystalline silicon' covers almost all "
                "modern residential panels; CIS and CdTe are thin-film types with "
                "slightly different temperature behaviour.",
            )
        with c4:
            mounting = st.radio(
                "Mounting", ["building", "free"], horizontal=True, key="mounting",
                help="'building' = fixed to a roof or façade (little airflow "
                "behind, so panels run warmer). 'free' = free-standing / ground "
                "mount with air circulating behind, which cools the panels.",
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

    # result.monthly is already in calendar order (month 1..12).
    month_order = [m.name for m in result.monthly]
    df = pd.DataFrame(
        {
            "Month": month_order,
            "Energy (kWh)": [m.energy_kwh for m in result.monthly],
            "Irradiation (kWh/m²)": [m.irradiation_kwh_m2 for m in result.monthly],
        }
    )

    st.subheader("Monthly energy production")
    # st.bar_chart sorts a string x-axis alphabetically; Altair with an explicit
    # `sort` keeps Jan→Dec order. width="container" fills the column responsively.
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Month:N", sort=month_order, title=None),
            y=alt.Y("Energy (kWh):Q"),
            tooltip=["Month", "Energy (kWh)", "Irradiation (kWh/m²)"],
        )
        .properties(width="container", height=320)
    )
    st.altair_chart(chart)

    with st.expander("Monthly detail & system losses"):
        st.caption(f"Total system losses applied: {result.total_loss_pct:.1f}%")
        st.dataframe(df.set_index("Month"), width="stretch")
