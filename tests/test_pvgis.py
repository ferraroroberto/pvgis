"""Unit tests for src/pvgis.py — the PVcalc response parser.

The HTTP call is stubbed so the suite is offline and deterministic; the
fixture mirrors the real v5_3 ``PVcalc`` JSON shape (totals.fixed,
monthly.fixed, inputs.location).
"""

from __future__ import annotations

import pytest
import requests

from src import pvgis

_FAKE_RESPONSE = {
    "inputs": {"location": {"latitude": 40.4, "longitude": -3.7, "elevation": 603}},
    "outputs": {
        "totals": {
            "fixed": {
                "E_d": 17.74,
                "E_m": 539.65,
                "E_y": 6475.78,
                "H(i)_y": 2093.1,
                "l_total": -22.65,
            }
        },
        "monthly": {
            "fixed": [
                {"month": i, "E_m": 400.0 + i, "H(i)_m": 100.0 + i}
                for i in range(1, 13)
            ]
        },
    },
}


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self._payload = payload
        self.status_code = status
        self.text = "ok"

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def raise_for_status(self) -> None:
        if not self.ok:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self) -> dict:
        return self._payload


def test_estimate_parses_totals_and_months(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        pvgis.requests, "get", lambda *a, **k: _FakeResponse(_FAKE_RESPONSE)
    )

    result = pvgis.estimate(lat=40.4, lon=-3.7, peakpower=4.0)

    assert result.yearly_energy_kwh == pytest.approx(6475.78)
    assert result.elevation_m == pytest.approx(603)
    assert len(result.monthly) == 12
    assert result.monthly[0].month == 1
    assert result.monthly[0].name == "Jan"
    assert result.monthly[11].name == "Dec"
    assert result.monthly[5].energy_kwh == pytest.approx(406.0)


def test_estimate_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        pvgis.requests, "get", lambda *a, **k: _FakeResponse({}, status=400)
    )

    with pytest.raises(requests.HTTPError):
        pvgis.estimate(lat=999.0, lon=999.0, peakpower=4.0)
