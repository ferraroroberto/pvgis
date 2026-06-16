# Project Instructions

Canonical instructions for AI coding agents working in this repository. Claude Code reads this file directly as project memory. Other agents (Cursor, Codex, etc.) reach it via the one-line `AGENTS.md` pointer.

## Streamlit conventions
*Apply only if this project uses Streamlit.*

- `st.set_page_config(layout="wide", page_title="...")` MUST be the first Streamlit call.
- Use `width="stretch"` (and `width="content"` where appropriate) in new and modified code. **Never** introduce new `use_container_width=True` — it is deprecated. When you touch existing code that uses `use_container_width`, migrate it.
- All mutable state in `st.session_state`. No module-level globals.
- `@st.cache_data` for DataFrames/files; `@st.cache_resource` for DB clients/models.
- Every widget needs a stable, explicit `key=`.
- UI code only in the UI directory (e.g. `app/`). Data logic stays in the non-UI package (e.g. `src/`). Never import `streamlit` from non-UI code.
- User feedback via `st.error()` / `st.warning()` / `st.success()`, not `st.write()`.
- **App layout:** main file (e.g. `app.py`) handles only page config, shared state, sidebar, and tab/radio routing. Each tab/mode lives in its own file exposing a `main(...)` (or `render_*`) function. Default to `st.tabs()`; use a sidebar radio only when asked.

## End-to-end UI testing
*Apply only if this project serves a browser UI (Streamlit, FastAPI, Flask, etc.).*

Two loops, kept deliberately separate. Don't conflate them. Full reasoning, setup, and bootstrap recipe in [`docs/playwright-ui-testing.md`](docs/playwright-ui-testing.md).

### Iterative verification (headed, agent-driven)
Use this during active development so I can watch the agent verify a change.

- Drive the running app via the **Playwright MCP server in `--headed` mode** (Claude Code, Codex CLI). For tools without MCP support, fall back to a small `playwright` Python script run via Bash with `headless=False` — same shape, just less ergonomic.
- Boot the app **once** on a fixed port (Streamlit default: 8501) and leave it running. Do NOT restart between iterations unless `set_page_config` or top-level imports changed.
- Prefer the a11y `snapshot` tool over `screenshot` — DOM is far cheaper than pixels in tokens. Screenshot only on failure or as final visual confirmation.
- Cap actions per cycle in the prompt (≤ 5 actions, then report). Stop and ask if the page state is unexpected; do not loop blindly.
- Target widgets via their stable `key=` (already required by Streamlit conventions above) using `page.get_by_role(..., name=...)` or `page.get_by_test_id(...)`.
- Do NOT create files under `tests/e2e/` for verification — it's throwaway, lives in the conversation only. Promotion to a permanent test is a separate, deliberate decision (see below).

### Regression suite (headless, pytest-playwright)
Optional. Lives at `tests/e2e/`. **Don't create the folder until the first regression test is actually justified.**

- Add a test only when all three hold: (1) silent breakage would hurt, (2) it can't be caught by a unit test under `tests/`, (3) the behavior has stabilized (not still in flux).
- Runs via `& .\.venv\Scripts\python.exe -m pytest tests/e2e/` (Windows) / `./.venv/bin/python -m pytest tests/e2e/` (POSIX). No LLM in the loop, zero per-run cost.
- **One shared session fixture boots the app — and any service dependencies** (a separate API process, a worker, a PTY host, …) — once per pytest run. Boot on a fixed or free port; **adopt** an instance already listening rather than spawning a second. The fixture is engine-agnostic: `streamlit run`, `uvicorn`, `flask run` are all just the launch command.
- **Boot failure is a hard failure — never `pytest.skip`.** A regression suite that skips when the app isn't up reports green on a build it never tested; that is the exact rot this suite exists to prevent. Skip is fine for the *ad-hoc* "use whatever tray I have running" path; the *pre-ship* path must fail loud.
- Keep the suite small — target < 15 tests total. If you're tempted to add #20, delete two first.
- No Page Object Model. Too much ceremony for this size.
- Don't gate commits on e2e. Run on push or in CI, not in pre-commit.
- When you remove a feature, remove its e2e test in the same commit.

### Mobile / phone-first UI testing
*Apply only if the app's primary surface is a phone.*

- Project the regression suite onto **WebKit** with a device-emulation descriptor (Playwright ships iPhone / Android descriptors — viewport, user-agent, touch, scale factor). WebKit shares the iOS Safari rendering + JS engine, so it reproduces the large majority of "Safari is unhappy" bugs on a Windows/Linux box, before they reach a real phone.
- Make the projection **always-on** — a parametrised `browser_name` / device fixture so every test runs the mobile projection too. An opt-in projection gets forgotten.
- WebKit-on-Windows is *not* real iOS: no iOS shell, no real WKWebView memory limits, no Apple keyboard, no Add-to-Home-Screen container. For the residual shell-only bugs, attach PC DevTools to a real phone via `ios-webkit-debug-proxy` (bridges the iOS Web Inspector to a local port Edge/Chrome DevTools can attach to). Playwright cannot drive real iOS Safari — only its bundled WebKit and the iOS Simulator on macOS.

## This repository
Streamlit app that estimates a house's solar-PV output via the EU JRC **PVGIS** non-interactive API (`PVcalc`) — free, no API key. It is a thin API *client*, not a fork of the PVGIS server (which would need terabyte-scale radiation databases). The API client lives in `src/pvgis.py`; the UI is the `PV Estimator` view in `app/views/`.

House-specific inputs (coordinates, system size) live in `.env` (gitignored) and feed `src/config.py`'s `HOME_*` defaults — the repo is public, so never commit real coordinates. See `README.md` for setup, layout, and usage.
