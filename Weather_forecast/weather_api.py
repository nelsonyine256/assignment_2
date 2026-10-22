"""Reusable helpers for Mini-Project 1: weather forecasts from Open-Meteo and MET Norway.

The notebook imports everything from here. Functions are split in two groups:

* network functions (geocode, get_forecast, fetch_met) that call request_json;
* pure parsing functions (parse_geocode, forecast_to_dataframe, met_to_daily)
  that only read JSON, so they can be tested offline with saved samples.
"""
import time
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo  # standard library: converts MET's UTC times to local time

import pandas as pd
import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

DAILY_VARIABLES = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"

# Weather code descriptions: WMO Weather interpretation codes (WW),
# as documented at https://open-meteo.com/en/docs
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherAPIError(Exception):
    """Raised when talking to a weather API fails for good (or input is invalid)."""


def build_headers(contact_email: str) -> dict:
    """Return request headers with the identifying User-Agent that MET Norway requires."""
    return {"User-Agent": f"UniWeatherAssignment/1.0 ({contact_email})"}


def request_json(url: str, params: Optional[dict] = None, headers: Optional[dict] = None,
                 timeout: float = 10, max_retries: int = 3, backoff: float = 0.5) -> Any:
    """GET a URL and return its JSON, retrying temporary failures.

    Waits backoff * 2**attempt seconds between tries (0.5s, 1s, 2s...).
    Connection errors, timeouts, HTTP 5xx and 429 are retried; other 4xx
    errors fail at once. Raises WeatherAPIError if every attempt fails.
    """
    last_error = None   # remember the most recent problem

    # range(max_retries + 1) -> first try + max_retries retries
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()      # 4xx/5xx -> raises HTTPError
            return response.json()           # success: leave the function here

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as exc:
            last_error = exc                 # temporary problem: try again

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code
            if status >= 500 or status == 429:
                last_error = exc             # server trouble / rate limit: try again
            else:
                # 400, 404...: OUR mistake, retrying won't help, stop immediately
                raise WeatherAPIError(f"HTTP {status}: request rejected") from exc

        except ValueError as exc:            # reply wasn't valid JSON
            raise WeatherAPIError("Reply was not valid JSON") from exc

        # We only reach here if the attempt failed and is retryable
        if attempt < max_retries:
            wait = backoff * (2 ** attempt)  # 0.5, 1.0, 2.0 ...
            print(f"Attempt {attempt + 1} failed, waiting {wait}s")
            time.sleep(wait)

    # Loop finished: every attempt failed
    raise WeatherAPIError(f"Gave up after {max_retries + 1} attempts: {last_error}") from last_error


def parse_geocode(data: dict) -> list:
    """Return the list of candidate places from geocoding JSON (no network)."""
    if "results" not in data:           # the key is absent when nothing matches
        raise WeatherAPIError("No place found with that name")
    return data["results"]


def geocode(name: str) -> list:
    """Return a list of candidate places for a city name."""
    if not name.strip():
        raise WeatherAPIError("City name is empty")
    data = request_json(GEOCODE_URL, params={"name": name, "count": 10, "language": "en"})
    return parse_geocode(data)


def get_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Return the daily Open-Meteo forecast JSON for the given coordinates."""
    if not -90 <= lat <= 90:
        raise WeatherAPIError(f"Latitude {lat} is outside -90..90")
    if not -180 <= lon <= 180:
        raise WeatherAPIError(f"Longitude {lon} is outside -180..180")
    if not 1 <= days <= 16:
        raise WeatherAPIError("days must be between 1 and 16")

    params = {
        "latitude": lat, "longitude": lon,
        "daily": DAILY_VARIABLES,
        "timezone": "auto",            # day boundaries follow the place's local time
        "forecast_days": days,
    }
    return request_json(FORECAST_URL, params=params)


def forecast_to_dataframe(payload: dict) -> pd.DataFrame:
    """Convert the Open-Meteo forecast JSON (a dict) into a pandas DataFrame."""
    daily = payload["daily"]
    units = payload["daily_units"]

    return pd.DataFrame({
        "Date": pd.to_datetime(daily["time"]),
        "Weather": [WMO_CODES.get(c, "Unknown") for c in daily["weather_code"]],
        f"Max temp ({units['temperature_2m_max']})": daily["temperature_2m_max"],
        f"Min temp ({units['temperature_2m_min']})": daily["temperature_2m_min"],
        f"Precipitation ({units['precipitation_sum']})": daily["precipitation_sum"],
        f"Max wind ({units['wind_speed_10m_max']})": daily["wind_speed_10m_max"],
    })


def fetch_met(lat: float, lon: float, headers: dict) -> dict:
    """Return the MET Norway forecast JSON (needs headers from build_headers)."""
    # MET asks for at most 4 decimals in coordinates; its parameter names are lat/lon
    params = {"lat": round(lat, 4), "lon": round(lon, 4)}
    return request_json(MET_URL, params=params, headers=headers)


def met_to_daily(payload: dict, tz_name: str) -> pd.DataFrame:
    """Group MET time steps into one row per local day (a DataFrame)."""
    zone = ZoneInfo(tz_name)
    days: dict = {}                    # date -> collected numbers

    for step in payload["properties"]["timeseries"]:
        # "2026-10-11T12:00:00Z" -> a datetime -> converted to local time
        utc_time = datetime.fromisoformat(step["time"].replace("Z", "+00:00"))
        day = utc_time.astimezone(zone).date()

        details = step["data"]["instant"]["details"]
        if day not in days:
            days[day] = {"temps": [], "winds": [], "rain": 0.0}

        days[day]["temps"].append(details["air_temperature"])
        days[day]["winds"].append(details["wind_speed"] * 3.6)    # m/s -> km/h

        # Use the 1-hour rain if present, else the 6-hour rain.
        # (Never both, or we'd count the same rain twice.)
        block = step["data"].get("next_1_hours") or step["data"].get("next_6_hours")
        if block:
            days[day]["rain"] += block["details"].get("precipitation_amount", 0.0)

    rows = []
    for day, v in sorted(days.items()):
        rows.append({
            "Date": pd.Timestamp(day),
            "Max temp (°C)": round(max(v["temps"]), 1),
            "Min temp (°C)": round(min(v["temps"]), 1),
            "Precipitation (mm)": round(v["rain"], 1),
            "Max wind (km/h)": round(max(v["winds"]), 1),
        })
    return pd.DataFrame(rows)
