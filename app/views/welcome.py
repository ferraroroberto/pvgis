"""Welcome / landing view."""

import streamlit as st

from src.config import APP_NAME


def render() -> None:
    st.title(f"👋 Welcome to {APP_NAME}")
    st.markdown(
        """
        Estimate the solar PV output of your house using the EU Joint
        Research Centre's **PVGIS** service — free, no API key.

        ### How it works
        This app calls the PVGIS *non-interactive* REST API (`PVcalc`).
        You give it a roof's **location**, **peak power**, **tilt** and
        **azimuth**; PVGIS returns the estimated **yearly and monthly
        energy production**, using its solar-radiation, temperature and
        wind databases. The numbers match the official web tool exactly.

        ### Try it
        Open the **☀ PV Estimator** view from the sidebar. The form is
        pre-filled from your `.env` (see `.env.example`) so your own
        house's coordinates stay out of version control.

        ### Layout
        - **`app/`** — Streamlit UI: entry point, views, theme.
        - **`src/`** — non-UI Python: `pvgis.py` API client, logger, config.
        - **`data/`** — working directory (`input/`, `output/`, `logs/`).

        See `README.md` for setup and `CLAUDE.md` for conventions.
        """
    )
