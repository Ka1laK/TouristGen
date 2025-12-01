from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pydantic import BaseModel
from app.services.weather_service import WeatherService

router = APIRouter()
weather_service = WeatherService()


class WeatherResponse(BaseModel):
    temperature: float
    precipitation: float
    wind_speed: float
    weather_code: int
    humidity: float
    description: str
    is_good_for_outdoor: bool


@router.get("/current", response_model=WeatherResponse)
def get_current_weather(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude")
):
    """Get current weather for a location"""
    try:
        weather_data = weather_service.get_current_weather(latitude, longitude)
        
        if not weather_data:
            raise HTTPException(status_code=404, detail="Weather data not available")
        
        description = weather_service.get_weather_description(weather_data["weather_code"])
        is_good = weather_service.is_good_weather_for_outdoor(weather_data)
        
        return WeatherResponse(
            **weather_data,
            description=description,
            is_good_for_outdoor=is_good
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get("/forecast")
def get_forecast(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    hours: int = Query(24, description="Number of hours to forecast", ge=1, le=72)
):
    """Get hourly weather forecast"""
    try:
        forecast = weather_service.get_hourly_forecast(latitude, longitude, hours)
        
        if not forecast:
            raise HTTPException(status_code=404, detail="Forecast data not available")
        
        return forecast
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")


@router.get("/penalty")
def calculate_weather_penalty(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    activity_type: str = Query(..., description="Activity type (outdoor, indoor, beach, etc.)")
):
    """Calculate weather penalty for an activity"""
    try:
        weather_data = weather_service.get_current_weather(latitude, longitude)
        
        if not weather_data:
            return {"penalty": 0.0, "message": "Weather data not available"}
        
        penalty = weather_service.calculate_weather_penalty(weather_data, activity_type)
        
        return {
            "penalty": penalty,
            "weather": weather_data,
            "activity_type": activity_type,
            "description": weather_service.get_weather_description(weather_data["weather_code"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating penalty: {str(e)}")
