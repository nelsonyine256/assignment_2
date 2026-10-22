"""Offline tests: they read saved JSON from sample_json/ and never touch the internet.

Run from the repository root with:  pytest
"""
import json
from pathlib import Path

import pytest

from src.weather_api import (
    WMO_CODES, WeatherAPIError, forecast_to_dataframe, get_forecast,
    met_to_daily, parse_geocode, request_json,
)
import src.weather_api as api

SAMPLES = Path(__file__).resolve().parent.parent / "sample_json"


def load(filename):
    """Read one saved sample JSON file."""
    with open(SAMPLES / filename, encoding="utf-8") as f:
        return json.load(f)


def test_geocode_returns_several_candidates():
    assert len(parse_geocode(load("geocode_sample.json"))) > 1


def test_geocode_without_results_key_raises():
    with pytest.raises(WeatherAPIError):
        parse_geocode(load("geocode_no_results.json"))


def test_forecast_dataframe_shape_and_logic():
    raw = load("forecast_sample.json")
    df = forecast_to_dataframe(raw)
    assert len(df) == len(raw["daily"]["time"])
    assert (df["Max temp (°C)"] >= df["Min temp (°C)"]).all()


def test_forecast_first_value_matches_raw_json():
    raw = load("forecast_sample.json")
    df = forecast_to_dataframe(raw)
    assert df["Max temp (°C)"].iloc[0] == raw["daily"]["temperature_2m_max"][0]


def test_weather_code_decoding():
    assert WMO_CODES[0] == "Clear sky"
    assert WMO_CODES.get(1234, "Unknown") == "Unknown"


def test_met_daily_aggregation():
    met_raw = load("met_sample.json")
    tz = load("forecast_sample.json")["timezone"]
    daily = met_to_daily(met_raw, tz)
    assert daily["Date"].is_monotonic_increasing
    assert (daily["Precipitation (mm)"] >= 0).all()
    first_wind = met_raw["properties"]["timeseries"][0]["data"]["instant"]["details"]["wind_speed"]
    assert daily["Max wind (km/h)"].max() >= round(first_wind * 3.6, 1) - 0.05


def test_malformed_forecast_raises_keyerror():
    with pytest.raises(KeyError):
        forecast_to_dataframe({"unexpected": 1})


def test_invalid_latitude_rejected_before_any_request():
    with pytest.raises(WeatherAPIError):
        get_forecast(123, 10)


class FakeResponse:
    """Pretend server reply with a chosen status code."""

    def __init__(self, status_code, payload=None):
        self.status_code, self.payload = status_code, payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.exceptions.HTTPError("error", response=self)

    def json(self):
        return self.payload


def test_retry_recovers_after_two_503s(monkeypatch):
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        return FakeResponse(503) if calls["n"] <= 2 else FakeResponse(200, {"ok": True})

    monkeypatch.setattr(api.requests, "get", flaky)
    assert request_json("https://example.com", backoff=0) == {"ok": True}
    assert calls["n"] == 3


def test_400_is_not_retried(monkeypatch):
    calls = {"n": 0}

    def bad(*args, **kwargs):
        calls["n"] += 1
        return FakeResponse(400)

    monkeypatch.setattr(api.requests, "get", bad)
    with pytest.raises(WeatherAPIError):
        request_json("https://example.com", backoff=0)
    assert calls["n"] == 1
