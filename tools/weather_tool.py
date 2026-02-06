"""
Weather Tool for AI Operations Assistant
Provides weather data using Open-Meteo API (free, no API key required)
"""

import requests
from typing import Dict, Any, Optional
from .base_tool import BaseTool


class WeatherTool(BaseTool):
    """Tool for fetching weather data using Open-Meteo API"""
    
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    
    def __init__(self):
        """Initialize Weather tool"""
        pass
    
    @property
    def name(self) -> str:
        return "weather"
    
    @property
    def description(self) -> str:
        return "Get current weather and forecast for any city worldwide"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["current", "forecast"],
                    "description": "Action to perform: 'current' for current weather, 'forecast' for 7-day forecast"
                },
                "city": {
                    "type": "string",
                    "description": "City name to get weather for"
                },
                "country": {
                    "type": "string",
                    "description": "Optional country code (e.g., 'US', 'IN', 'UK') to disambiguate city names"
                }
            },
            "required": ["action", "city"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute weather API action"""
        action = kwargs.get("action", "current")
        city = kwargs.get("city", "")
        country = kwargs.get("country")
        
        if not city:
            return {
                "success": False,
                "data": None,
                "error": "City name is required"
            }
        
        try:
            # First, geocode the city to get coordinates
            coords = self._geocode_city(city, country)
            if not coords:
                return {
                    "success": False,
                    "data": None,
                    "error": f"Could not find city: {city}"
                }
            
            if action == "current":
                return self._get_current_weather(coords)
            elif action == "forecast":
                return self._get_forecast(coords)
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    def _geocode_city(self, city: str, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Convert city name to coordinates"""
        params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        response = requests.get(self.GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return None
        
        # If country specified, try to match
        if country:
            for result in results:
                if result.get("country_code", "").upper() == country.upper():
                    return {
                        "lat": result["latitude"],
                        "lon": result["longitude"],
                        "name": result["name"],
                        "country": result.get("country", "Unknown"),
                        "timezone": result.get("timezone", "UTC")
                    }
        
        # Return first result
        result = results[0]
        return {
            "lat": result["latitude"],
            "lon": result["longitude"],
            "name": result["name"],
            "country": result.get("country", "Unknown"),
            "timezone": result.get("timezone", "UTC")
        }
    
    def _get_current_weather(self, coords: Dict[str, Any]) -> Dict[str, Any]:
        """Get current weather for coordinates"""
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": coords.get("timezone", "UTC")
        }
        
        response = requests.get(self.WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        
        return {
            "success": True,
            "data": {
                "location": {
                    "city": coords["name"],
                    "country": coords["country"],
                    "coordinates": {
                        "lat": coords["lat"],
                        "lon": coords["lon"]
                    }
                },
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "temperature_unit": "°C",
                    "feels_like": current.get("apparent_temperature"),
                    "humidity": current.get("relative_humidity_2m"),
                    "humidity_unit": "%",
                    "precipitation": current.get("precipitation"),
                    "precipitation_unit": "mm",
                    "wind_speed": current.get("wind_speed_10m"),
                    "wind_speed_unit": "km/h",
                    "wind_direction": current.get("wind_direction_10m"),
                    "weather_code": current.get("weather_code"),
                    "weather_description": self._get_weather_description(current.get("weather_code"))
                }
            },
            "error": None
        }
    
    def _get_forecast(self, coords: Dict[str, Any]) -> Dict[str, Any]:
        """Get 7-day weather forecast for coordinates"""
        params = {
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,wind_speed_10m_max",
            "timezone": coords.get("timezone", "UTC")
        }
        
        response = requests.get(self.WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        
        forecast_days = []
        for i, date in enumerate(dates):
            forecast_days.append({
                "date": date,
                "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else None,
                "wind_speed_max": daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else None,
                "weather_code": daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else None,
                "weather_description": self._get_weather_description(
                    daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else None
                )
            })
        
        return {
            "success": True,
            "data": {
                "location": {
                    "city": coords["name"],
                    "country": coords["country"],
                    "coordinates": {
                        "lat": coords["lat"],
                        "lon": coords["lon"]
                    }
                },
                "forecast": forecast_days,
                "units": {
                    "temperature": "°C",
                    "precipitation": "mm",
                    "wind_speed": "km/h"
                }
            },
            "error": None
        }
    
    def _get_weather_description(self, code: Optional[int]) -> str:
        """Convert WMO weather code to description"""
        if code is None:
            return "Unknown"
        
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        return weather_codes.get(code, f"Unknown (code: {code})")
