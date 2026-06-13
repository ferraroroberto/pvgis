"""Session fixtures for the headless e2e regression suite.

`streamlit_app` force-restarts Streamlit against the current code on disk
(see `tests/_streamlit_lifecycle.py`) so the suite can never pass against a
stale process. `pytest-playwright` supplies the `page` fixture.

The webapp uses no TLS locally, so no `browser_context_args` override is
needed — unlike a self-signed-cert project, which would add
`ignore_https_errors` here.
"""

from __future__ import annotations

import os
from typing import Iterator

import pytest
from playwright.sync_api import Page

from tests._streamlit_lifecycle import (
    STREAMLIT_E2E_PORT,
    ensure_fresh_streamlit,
    kill_streamlit_on_port,
)

# Bounded default timeout for auto-waiting actions (click, goto, wait_for_selector …).
# Without an explicit cap, Playwright falls back to 30 s — a silent, opaque hang that
# stacks into multi-minute CI failures.  15 s self-names the locator on failure fast
# enough to be useful.  Override via E2E_DEFAULT_TIMEOUT_MS env var.  (#7)
_DEFAULT_TIMEOUT_MS = int(os.environ.get("E2E_DEFAULT_TIMEOUT_MS", "15000"))


@pytest.fixture(autouse=True)
def _bound_default_timeouts(page: Page) -> None:
    """Apply a bounded, tunable default timeout to every test's page. (#7)"""
    page.set_default_timeout(_DEFAULT_TIMEOUT_MS)
    page.set_default_navigation_timeout(_DEFAULT_TIMEOUT_MS)


@pytest.fixture(scope="session")
def streamlit_app() -> Iterator[str]:
    """Boot a fresh Streamlit for the whole pytest session; kill it after."""
    base_url = ensure_fresh_streamlit(STREAMLIT_E2E_PORT)
    try:
        yield base_url
    finally:
        kill_streamlit_on_port(STREAMLIT_E2E_PORT)
