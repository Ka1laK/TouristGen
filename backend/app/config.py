from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database
    database_url: str = "sqlite:///./database/touristgen.db"
    
    # API Keys (optional)
    openrouteservice_api_key: str = ""
    google_maps_api_key: str = ""
    openweather_api_key: str = "" # Ya no se usa
    
    # Application
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8004
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000"
    ]
    
    # Genetic Algorithm defaults (optimized for fast response)
    ga_population_size: int = 30
    ga_generations: int = 30
    ga_mutation_rate: float = 0.15
    ga_crossover_rate: float = 0.8
    
    # Scraper settings
    scraper_rate_limit: float = 1.0  # seconds between requests
    scraper_timeout: int = 10  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
