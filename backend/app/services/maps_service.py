"""
Super-Agente de Extracción usando Places API (New)
Lima Metropolitana + Callao

Integrado con TouristGen Backend
"""

import requests
import json
import time
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models.poi import POI

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL de la nueva Places API
PLACES_API_BASE = "https://places.googleapis.com/v1/places"

# 43 distritos de Lima + Callao
DISTRICTS = [
    # Lima Centro
    "Lima Cercado", "Breña", "La Victoria", "Rímac",
    # Lima Norte
    "Ancón", "Carabayllo", "Comas", "Independencia", "Los Olivos",
    "Puente Piedra", "San Martín de Porres", "Santa Rosa",
    # Lima Este
    "Ate", "Chaclacayo", "Cieneguilla", "El Agustino", "Lurigancho",
    "San Juan de Lurigancho", "San Luis", "Santa Anita",
    # Lima Sur
    "Chorrillos", "Lurín", "Pachacámac", "Pucusana", "Punta Hermosa",
    "Punta Negra", "San Bartolo", "San Juan de Miraflores",
    "Santa María del Mar", "Villa El Salvador", "Villa María del Triunfo",
    # Lima Moderna
    "Barranco", "Jesús María", "La Molina", "Lince", "Magdalena del Mar",
    "Miraflores", "Pueblo Libre", "San Borja", "San Isidro",
    "San Miguel", "Santiago de Surco", "Surquillo",
    # Callao
    "Callao"
]

# Mapeo de categorías a términos de búsqueda
CATEGORY_SEARCH_TERMS = {
    "Museum": ["museo", "galería de arte", "museum"],
    "Park": ["parque", "park", "área verde"],
    "Beach": ["playa", "beach"],
    "Shopping": ["centro comercial", "mall", "shopping"],
    "Dining": ["restaurante", "restaurant"],
    "Religious": ["iglesia", "catedral", "templo"],
    "Landmark": ["monumento", "atractivo turístico", "landmark"],
    "Zoo": ["zoológico", "zoo"],
    "Cultural": ["centro cultural", "cultural center"],
    "Coffee Shops": ["cafetería", "café", "coffee shop"]
}

# Dynamic category mapping rules (priority order - first match wins)
# Each rule: (CategoryName, [keywords to match in Google types])
CATEGORY_RULES = [
    ("Museum", ["museum", "gallery", "art_", "cultural_center", "heritage"]),
    ("Park", ["park", "garden", "nature", "forest", "botanical", "playground"]),
    ("Beach", ["beach", "coast", "shore", "playa", "seaside"]),
    ("Zoo", ["zoo", "aquarium", "animal", "wildlife"]),
    ("Shopping", ["mall", "shopping", "store", "market", "comercial", "supermarket"]),
    ("Dining", ["restaurant", "cafe", "coffee", "bar", "food", "bakery", "meal"]),
    ("Religious", ["church", "temple", "mosque", "cathedral", "worship", "religious"]),
    ("Cultural", ["theater", "theatre", "cinema", "concert", "performing_arts"]),
    ("Landmark", ["landmark", "monument", "historic", "stadium", "tourist_attraction", "point_of_interest"]),
]


def map_google_types_to_category(types: list) -> str:
    """
    Dynamic keyword matching for category assignment.
    Joins all types into a string and checks if any keyword is present.
    Returns first matching category (priority order).
    """
    if not types:
        return "Landmark"
    
    types_str = " ".join(types).lower()
    
    for category, keywords in CATEGORY_RULES:
        if any(kw in types_str for kw in keywords):
            return category
    
    return "Landmark"  # Default fallback


# ==================== FUNCIONES API (NEW) ====================


def search_text_new_api(query: str, api_key: str) -> List[Dict]:
    """
    Búsqueda usando Places API (New) - Text Search
    Documentación: https://developers.google.com/maps/documentation/places/web-service/text-search
    """
    url = f"{PLACES_API_BASE}:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.regularOpeningHours,places.types,places.websiteUri,places.internationalPhoneNumber"
    }
    
    data = {
        "textQuery": query,
        "languageCode": "es"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("places", [])
        else:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            logger.error(f"API Error: {error_msg}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error: {str(e)}")
        return []
    except json.JSONDecodeError:
        logger.error("JSON Decode Error")
        return []


class LimaPlacesExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.google_maps_api_key
        if not self.api_key:
            # Fallback warning, though script might fail if calls are made
            logger.warning("Google Maps API Key is missing in configuration.")
            
        self.all_data = {}
        self.processed_places = set()
        
    def extract_and_populate_db(self, districts: List[str] = None, categories: Dict[str, List[str]] = None):
        """
        Extracts places for given districts and populates the database directly.
        Includes stale data cleanup logic.
        """
        districts = districts or DISTRICTS
        categories = categories or CATEGORY_SEARCH_TERMS
        
        db = SessionLocal()
        total_added = 0
        total_updated = 0
        
        # Mark start time of this full synchronization session
        sync_start_time = datetime.utcnow()
        
        try:
            for district in districts:
                logger.info(f"Processing district: {district}")
                district_data = self.extract_district(district, categories)
                
                # Sync into DB immediately per district
                added, updated = self.sync_to_database(db, district_data["places"])
                total_added += added
                total_updated += updated
                
                logger.info(f"District {district} complete. Added: {added}, Updated: {updated}")
            
            # After processing all districts in the list, cleanup stale POIs IN THOSE DISTRICTS
            # Note: We only cleanup districts we actually scanned to avoid accidental deletions of non-scanned areas
            deactivated_count = self.cleanup_stale_pois(db, districts, sync_start_time)
            logger.info(f"Cleanup complete. Deactivated {deactivated_count} stale POIs.")
                
        except Exception as e:
            logger.error(f"Error during population: {e}")


    def extract_district(self, district: str, categories: Dict[str, List[str]]) -> Dict:
        """Extrae todos los lugares de un distrito"""
        places = []
        
        for category_name, search_terms in categories.items():
            # logger.info(f"  Searching: {category_name} in {district}...")
            
            category_places = self.search_places_by_category(
                district=district,
                category_name=category_name,
                search_terms=search_terms
            )
            
            places.extend(category_places)
            time.sleep(1) # Rate limiting
        
        return {
            "district": district,
            "places": places
        }
    
    def search_places_by_category(self, district: str, category_name: str, search_terms: List[str]) -> List[Dict]:
        """Busca lugares por categoría"""
        places = []
        seen_names = set()
        
        for term in search_terms:
            query = f"{term} {district} Lima"
            results = search_text_new_api(query, self.api_key)
            
            for place in results:
                place_id = place.get('id')
                if place_id in self.processed_places:
                    continue
                
                # Simple deduplication by name
                display_name = place.get('displayName', {})
                place_name = display_name.get('text') if isinstance(display_name, dict) else str(display_name)
                
                if place_name in seen_names:
                    continue
                
                # District validation
                if not self.is_in_district(place, district):
                    continue
                
                place_data = self.normalize_place_data(place, category_name, district)
                
                if place_data and self.validate_place(place_data):
                    places.append(place_data)
                    self.processed_places.add(place_id)
                    seen_names.add(place_name)
            
            time.sleep(0.5)
        
        return places
    
    def is_in_district(self, place: Dict, district: str) -> bool:
        """Verifica si el lugar está en el distrito"""
        address = place.get('formattedAddress', '').lower()
        district_clean = district.lower()
        
        if district_clean in address:
            return True
        
        # Variaciones comunes y combinadas para Lima
        variations = {
            "lima cercado": ["cercado de lima", "lima centro", "lima 15001"],
            "callao": ["callao", "bellavista", "la punta"],
            "san juan de lurigancho": ["sjl"],
            "san juan de miraflores": ["sjm"],
            "villa el salvador": ["ves"],
            "villa maría del triunfo": ["vmt"],
            "santiago de surco": ["surco"],
            "la victoria": ["victoria"],
            "san martín de porres": ["smp"]
        }
        
        # Check variations
        if district.lower() in variations:
            if any(v in address for v in variations[district.lower()]):
                return True
                
        # Fallback: if district name is compound (e.g. San Miguel), check just the name
        if district_clean in address:
            return True

        return False
    
    def normalize_place_data(self, place: Dict, category: str, district: str) -> Optional[Dict]:
        """Normaliza los datos al formato del modelo POI"""
        try:
            display_name = place.get('displayName', {})
            name = display_name.get('text') if isinstance(display_name, dict) else str(display_name)
            
            location = place.get('location', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            
            price_level_raw = place.get('priceLevel', 'PRICE_LEVEL_FREE')
            price_level = self.convert_price_level(price_level_raw)
            
            rating = place.get('rating')
            user_ratings = place.get('userRatingCount', 0)
            
            # Additional fields
            address = place.get('formattedAddress', '')
            website = place.get('websiteUri', '')
            phone = place.get('internationalPhoneNumber', '')
            
            place_data = {
                "name": name,
                "category": category,
                "district": district,
                "latitude": latitude,
                "longitude": longitude,
                "address": address,
                "description": self.generate_description(name, rating, user_ratings, category),
                "price_level": price_level,
                "rating": rating if rating else 0.0,
                "popularity": min(100, int(user_ratings / 10)) if user_ratings else 50, # Basic logic
                "visit_duration": self.estimate_duration(category),
                "opening_hours": self.parse_opening_hours_new(place.get('regularOpeningHours')),
                "tags": self.generate_tags(place, category, price_level),
                "website": website,
                "phone": phone,
                "image_url": None # Places API charges extra for photos
            }
            
            return place_data
            
        except Exception as e:
            logger.error(f"Error normalizing place: {e}")
            return None
    
    def convert_price_level(self, price_str: str) -> int:
        mapping = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4
        }
        return mapping.get(price_str, 0)
    
    def generate_description(self, name: str, rating: Optional[float], user_ratings: int, category: str) -> str:
        desc = f"{name} en {category}."
        if rating and user_ratings:
            desc += f" Valorado con {rating} estrellas ({user_ratings} reseñas)."
        return desc
    
    def estimate_duration(self, category: str) -> int:
        durations = {
            "Museum": 90, "Park": 60, "Beach": 180, "Shopping": 120,
            "Dining": 90, "Religious": 30, "Landmark": 45, "Zoo": 150,
            "Cultural": 75, "Coffee Shops": 45
        }
        return durations.get(category, 60)
    
    def parse_opening_hours_new(self, opening_hours: Optional[Dict]) -> Dict[str, str]:
        """
        Parse opening hours from Google Places API (New) format.
        Returns a dict with day names as keys and time ranges as values.
        """
        default_hours = {
            "Monday": None, "Tuesday": None, "Wednesday": None,
            "Thursday": None, "Friday": None, "Saturday": None, "Sunday": None
        }
        
        if not opening_hours:
            return default_hours
        
        # Try weekdayDescriptions first (human readable format)
        if 'weekdayDescriptions' in opening_hours:
            day_mapping = {
                'lunes': 'Monday', 'martes': 'Tuesday', 'miércoles': 'Wednesday',
                'jueves': 'Thursday', 'viernes': 'Friday', 'sábado': 'Saturday',
                'domingo': 'Sunday',
                # Also support English
                'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday',
                'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday',
                'sunday': 'Sunday'
            }
            
            for text in opening_hours.get('weekdayDescriptions', []):
                text_lower = text.lower()
                
                for spanish, english in day_mapping.items():
                    if spanish in text_lower:
                        # Check if closed
                        if 'cerrado' in text_lower or 'closed' in text_lower:
                            default_hours[english] = "Cerrado"
                        elif 'abierto 24 horas' in text_lower or 'open 24 hours' in text_lower:
                            default_hours[english] = "24 horas"
                        else:
                            # Extract time part after the day name
                            # Format is usually: "lunes: 9:00 a.m.–6:00 p.m."
                            if ':' in text:
                                # Get everything after the first colon
                                time_part = text.split(':', 1)[-1].strip()
                                if time_part:
                                    default_hours[english] = time_part
                        break
        
        # Also try 'periods' format (structured data)
        if 'periods' in opening_hours:
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for period in opening_hours.get('periods', []):
                open_info = period.get('open', {})
                close_info = period.get('close', {})
                
                day_idx = open_info.get('day', 0)
                if 0 <= day_idx < 7:
                    day_name = day_names[day_idx]
                    
                    open_hour = open_info.get('hour', 0)
                    open_min = open_info.get('minute', 0)
                    close_hour = close_info.get('hour', 0) if close_info else 23
                    close_min = close_info.get('minute', 0) if close_info else 59
                    
                    time_str = f"{open_hour:02d}:{open_min:02d} - {close_hour:02d}:{close_min:02d}"
                    default_hours[day_name] = time_str
        
        return default_hours

    
    def generate_tags(self, place: Dict, category: str, price_level: int) -> List[str]:
        tags = []
        category_tags = {
            "Museum": ["cultura", "arte", "historia"],
            "Park": ["naturaleza", "aire_libre", "familia"],
            "Beach": ["playa", "verano", "costa"],
            "Shopping": ["compras", "tiendas"],
            "Dining": ["gastronomia", "restaurante"],
            "Religious": ["religion", "templo"],
            "Landmark": ["turismo", "punto_interes"],
            "Zoo": ["animales", "familia"],
            "Cultural": ["cultura", "eventos"],
            "Coffee Shops": ["cafe", "bebidas"]
        }
        tags.extend(category_tags.get(category, [])[:3])
        if price_level == 0: tags.append("gratuito")
        elif price_level >= 3: tags.append("premium")
        return tags[:6]
    
    def validate_place(self, place: Dict) -> bool:
        if not place.get('name') or not place.get('latitude') or not place.get('longitude'):
            return False
        return True

    def sync_to_database(self, db: Session, places_data: List[Dict]) -> Tuple[int, int]:
        """
        Inserts or updates places in the SQLite database.
        Returns: (added_count, updated_count)
        """
        added = 0
        updated = 0
        now = datetime.utcnow()
        
        for p_data in places_data:
            # Check if exists by name and district
            existing_poi = db.query(POI).filter(
                POI.name == p_data["name"],
                POI.district == p_data["district"]
            ).first()
            
            if existing_poi:
                # Update existing
                for key, value in p_data.items():
                    if hasattr(existing_poi, key):
                         setattr(existing_poi, key, value)
                
                # Update timestamp and reactivate if it was inactive
                existing_poi.last_synced_at = now
                existing_poi.is_active = True
                
                updated += 1
            else:
                # Create new
                new_poi = POI(**p_data)
                new_poi.last_synced_at = now
                new_poi.is_active = True
                db.add(new_poi)
                added += 1
        
        db.commit()
        return added, updated

    def cleanup_stale_pois(self, db: Session, target_districts: List[str], cutoff_time: datetime) -> int:
        """
        Deactivates POIs in the target districts that were NOT updated after the cutoff_time.
        """
        count = 0
        stale_pois = db.query(POI).filter(
            POI.district.in_(target_districts),
            POI.is_active == True,
            (POI.last_synced_at < cutoff_time) | (POI.last_synced_at == None)
        ).all()
        
        for poi in stale_pois:
            poi.is_active = False
            count += 1
            
        db.commit()
        return count

    def fetch_pois_by_coordinates(self, lat: float, lng: float, radius: int = 1000) -> int:
        """
        Fetch POIs near a specific coordinate with radius expansion logic.
        """
        if not self.api_key:
            logger.error("No API key available for coordinate fetch")
            return 0
            
        total_added = 0
        total_updated = 0
        
        # Try expanding radius if no results: Start with 2.5km (covers most districts from center) -> 5km
        radii_to_try = [2500, 5000]
        
        for r in radii_to_try:
            logger.info(f"Fetching POIs at {lat}, {lng} with radius {r}m")
            
            # API endpoint for New Places API - Search Nearby
            url = f"{PLACES_API_BASE}:searchNearby"
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types,places.rating,places.userRatingCount,places.priceLevel,places.regularOpeningHours,places.websiteUri,places.internationalPhoneNumber,places.id"
            }
            
            # Categories to include - Using valid types for Google Places API (New)
            # See: https://developers.google.com/maps/documentation/places/web-service/place-types
            included_types = [
                "museum", "art_gallery", "tourist_attraction", "park", 
                "shopping_mall", "restaurant", "cafe", "bar",
                "amusement_park", "aquarium", "zoo", "stadium"
            ]
            
            body = {
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": lat,
                            "longitude": lng
                        },
                        "radius": float(r)
                    }
                },
                "includedTypes": included_types,
                "maxResultCount": 20,
                "rankPreference": "POPULARITY"
            }
            
            try:
                response = requests.post(url, headers=headers, json=body, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"Google API Error ({response.status_code}): {response.text}")
                    continue
                    
                data = response.json()
                places = data.get("places", [])
                
                if not places:
                    logger.info(f"No places found at radius {r}m. Expanding...")
                    continue
                
                logger.info(f"Found {len(places)} places at radius {r}m. Processing...")
                
                # Transform data
                processed_places = []
                for p in places:
                    # Get types from Google response
                    types = p.get("types", [])
                    
                    # Use dynamic category mapping
                    category = map_google_types_to_category(types)
                    
                    # Extract district from address
                    addr = p.get("formattedAddress", "")
                    district = "Lima"  # Default
                    for dist in DISTRICTS:
                        if dist in addr:
                            district = dist
                            break
                    
                    # Normalize with proper category and district
                    transformed = self.normalize_place_data(p, category, district)
                    
                    if transformed:
                        logger.info(f"Mapped POI '{transformed['name']}' -> Category: {category}, District: {district}")
                        processed_places.append(transformed)
                
                # Sync into DB
                db_gen = SessionLocal() # Use session factory manually
                try:
                    added, updated = self.sync_to_database(db_gen, processed_places)
                    total_added += added
                    total_updated += updated
                finally:
                    db_gen.close()
                
                if len(places) >= 3:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching by coordinates: {e}")
                
        logger.info(f"Coordinate fetch complete. Added: {total_added}, Updated: {total_updated}")
        return total_added + total_updated

# CLI for manual triggering
if __name__ == "__main__":
    import sys
    
    print("Starting extraction...")
    extractor = LimaPlacesExtractor()
    
    # Optional: simple command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
         # Just a small subset for testing
         districts = ["San Miguel", "Magdalena del Mar"]
    else:
         districts = DISTRICTS

    result = extractor.extract_and_populate_db(districts=districts)
    print(f"Extraction complete. Added: {result['added']}, Updated: {result['updated']}")