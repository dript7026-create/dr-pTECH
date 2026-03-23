from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import requests

from .media_signals import fixture_key


@dataclass
class OpenWeatherSource:
    api_key: Optional[str] = None
    base_url: str = "https://api.openweathermap.org/data/3.0/onecall"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("OPENWEATHER_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def fetch_daily_context(self, latitude: float, longitude: float) -> Dict[str, object]:
        response = requests.get(
            self.base_url,
            params={
                "lat": latitude,
                "lon": longitude,
                "units": "metric",
                "exclude": "minutely,current,alerts",
                "appid": self.api_key,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


def _severity_score(wind_speed: float, precipitation: float, temperature: float) -> float:
    wind_penalty = max(0.0, wind_speed - 8.0) * 0.06
    rain_penalty = precipitation * 0.08
    cold_penalty = max(0.0, 4.0 - temperature) * 0.03
    heat_penalty = max(0.0, temperature - 28.0) * 0.02
    return float(np.clip(wind_penalty + rain_penalty + cold_penalty + heat_penalty, 0.0, 0.45))


def build_fixture_weather_frame(fixtures_df: pd.DataFrame, source: Optional[OpenWeatherSource] = None) -> pd.DataFrame:
    weather_source = source or OpenWeatherSource()
    rows: List[Dict[str, object]] = []
    for fixture in fixtures_df.itertuples(index=False):
        fixture_row = {
            "fixture_key": fixture_key(fixture.home_team, fixture.away_team, fixture.date),
            "weather_temperature_c": 0.0,
            "weather_wind_speed": 0.0,
            "weather_precipitation_mm": 0.0,
            "weather_severity": 0.0,
            "weather_summary": "unavailable",
        }
        latitude = getattr(fixture, "latitude", None)
        longitude = getattr(fixture, "longitude", None)
        if not weather_source.is_configured or latitude in (None, "", np.nan) or longitude in (None, "", np.nan):
            rows.append(fixture_row)
            continue
        try:
            payload = weather_source.fetch_daily_context(float(latitude), float(longitude))
            daily = (payload.get("daily") or [{}])[0]
            temperature = float(((daily.get("temp") or {}).get("day", 0.0)) or 0.0)
            wind_speed = float(daily.get("wind_speed") or 0.0)
            precipitation = float(daily.get("rain") or daily.get("snow") or 0.0)
            weather = (daily.get("weather") or [{}])[0]
            fixture_row.update(
                {
                    "weather_temperature_c": temperature,
                    "weather_wind_speed": wind_speed,
                    "weather_precipitation_mm": precipitation,
                    "weather_severity": _severity_score(wind_speed, precipitation, temperature),
                    "weather_summary": weather.get("description") or "forecast",
                }
            )
        except requests.RequestException:
            pass
        rows.append(fixture_row)
    return pd.DataFrame(rows)