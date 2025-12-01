import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Weather service using Open-Meteo API (free, no API key required)
    https://open-meteo.com/
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.cache = {}  # Simple cache for weather data
        self.cache_duration = 3600  # 1 hour cache
    
    def get_hourly_forecast(
        self, 
        latitude: float, 
        longitude: float, 
        hours: int = 24
    ) -> Optional[Dict]:
        """
        Get hourly weather forecast for a location
        
        Returns:
            {
                "hourly": {
                    "time": [...],
                    "temperature_2m": [...],
                    "precipitation": [...],
                    "windspeed_10m": [...],
                    "weathercode": [...]
                }
            }
        """
        cache_key = f"{latitude:.4f},{longitude:.4f}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return cached_data
        
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,precipitation,windspeed_10m,weathercode,relativehumidity_2m",
                "forecast_days": 3,
                "timezone": "America/Lima"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the result
            self.cache[cache_key] = (data, datetime.now())
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
    
    def get_current_weather(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict]:
        """
        Get current weather conditions
        
        Returns:
            {
                "temperature": float,
                "precipitation": float,
                "wind_speed": float,
                "weather_code": int,
                "humidity": float
            }
        """
        forecast = self.get_hourly_forecast(latitude, longitude, hours=1)
        
        if not forecast or "hourly" not in forecast:
            return None
        
        hourly = forecast["hourly"]
        
        # Get current hour data (first entry)
        return {
            "temperature": hourly["temperature_2m"][0] if hourly["temperature_2m"] else 20,
            "precipitation": hourly["precipitation"][0] if hourly["precipitation"] else 0,
            "wind_speed": hourly["windspeed_10m"][0] if hourly["windspeed_10m"] else 0,
            "weather_code": hourly["weathercode"][0] if hourly["weathercode"] else 0,
            "humidity": hourly.get("relativehumidity_2m", [50])[0]
        }
    
    def get_weather_at_time(
        self,
        latitude: float,
        longitude: float,
        target_time: datetime
    ) -> Optional[Dict]:
        """Get weather forecast for a specific time"""
        forecast = self.get_hourly_forecast(latitude, longitude, hours=72)
        
        if not forecast or "hourly" not in forecast:
            return None
        
        hourly = forecast["hourly"]
        times = hourly["time"]
        
        # Find closest time
        target_str = target_time.strftime("%Y-%m-%dT%H:00")
        
        try:
            idx = times.index(target_str)
        except ValueError:
            # If exact time not found, use current weather
            return self.get_current_weather(latitude, longitude)
        
        return {
            "temperature": hourly["temperature_2m"][idx],
            "precipitation": hourly["precipitation"][idx],
            "wind_speed": hourly["windspeed_10m"][idx],
            "weather_code": hourly["weathercode"][idx],
            "humidity": hourly.get("relativehumidity_2m", [50])[idx]
        }
    
    def calculate_weather_penalty(
        self, 
        weather_data: Dict, 
        activity_type: str
    ) -> float:
        """
        Calculate penalty for outdoor activities based on weather
        
        Args:
            weather_data: Weather information
            activity_type: Type of activity (outdoor, indoor, beach, etc.)
        
        Returns:
            Penalty multiplier (0.0 = no penalty, 1.0 = maximum penalty)
        """
        penalty = 0.0
        
        if not weather_data:
            return penalty
        
        precipitation = weather_data.get("precipitation", 0)
        temperature = weather_data.get("temperature", 20)
        wind_speed = weather_data.get("wind_speed", 0)
        
        # Rain penalties
        if precipitation > 5:  # Heavy rain (mm/hour)
            if activity_type in ["outdoor", "park", "beach"]:
                penalty += 0.7
            elif activity_type in ["walking"]:
                penalty += 0.5
        elif precipitation > 2:  # Light rain
            if activity_type in ["outdoor", "park", "beach"]:
                penalty += 0.4
            elif activity_type in ["walking"]:
                penalty += 0.2
        
        # Temperature penalties
        if temperature > 32:  # Very hot
            if activity_type in ["outdoor", "walking"]:
                penalty += 0.3
        elif temperature < 12:  # Cold
            if activity_type in ["beach"]:
                penalty += 0.5
        
        # Wind penalties
        if wind_speed > 40:  # Strong wind (km/h)
            if activity_type in ["beach", "outdoor"]:
                penalty += 0.3
        
        return min(penalty, 1.0)  # Cap at 1.0
    
    def get_weather_description(self, weather_code: int) -> str:
        """
        Convert WMO weather code to description
        https://open-meteo.com/en/docs
        """
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
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
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
        
        return weather_codes.get(weather_code, "Unknown")
    
    def is_good_weather_for_outdoor(self, weather_data: Dict) -> bool:
        """Check if weather is suitable for outdoor activities"""
        if not weather_data:
            return True
        
        precipitation = weather_data.get("precipitation", 0)
        temperature = weather_data.get("temperature", 20)
        wind_speed = weather_data.get("wind_speed", 0)
        
        # Good weather conditions
        return (
            precipitation < 2 and  # Little to no rain
            15 < temperature < 30 and  # Comfortable temperature
            wind_speed < 30  # Not too windy
        )
