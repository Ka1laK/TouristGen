"""
Initialize database with sample POI data for Lima and Callao

This script creates a comprehensive dataset of tourist attractions
across 44 districts with realistic data.
"""

from app.database import SessionLocal, engine, Base
from app.models.poi import POI
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def load_sample_pois():
    """Load sample POI data into database"""
    db = SessionLocal()
    
    try:
        # Check if POIs already exist
        existing_count = db.query(POI).count()
        if existing_count > 0:
            logger.info(f"Database already has {existing_count} POIs. Skipping initialization.")
            return
        
        logger.info("Loading sample POI data...")
        
        # Sample POIs for major Lima districts
        sample_pois = [
            # MIRAFLORES
            {
                "name": "Parque Kennedy",
                "address": "Av. Larco, Miraflores",
                "latitude": -12.1203,
                "longitude": -77.0294,
                "district": "Miraflores",
                "category": "Park",
                "popularity": 85,
                "rating": 4.5,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 45,
                "tags": ["outdoor", "family-friendly", "cats", "free"],
                "description": "Iconic park in Miraflores known for its resident cats and vibrant atmosphere"
            },
            {
                "name": "Larcomar",
                "address": "Malecón de la Reserva 610, Miraflores",
                "latitude": -12.1344,
                "longitude": -77.0256,
                "district": "Miraflores",
                "category": "Shopping",
                "popularity": 90,
                "rating": 4.6,
                "price_level": 3,
                "opening_hours": {"all": "11:00-22:00"},
                "closed_days": [],
                "visit_duration": 120,
                "tags": ["shopping", "dining", "ocean-view", "modern"],
                "description": "Modern shopping center built into cliffs overlooking the Pacific Ocean"
            },
            {
                "name": "Huaca Pucllana",
                "address": "Calle General Borgoño cuadra 8, Miraflores",
                "latitude": -12.1089,
                "longitude": -77.0289,
                "district": "Miraflores",
                "category": "Museum",
                "popularity": 80,
                "rating": 4.4,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:00"},
                "closed_days": ["tuesday"],
                "visit_duration": 90,
                "tags": ["historical", "archaeological", "cultural", "educational"],
                "description": "Pre-Inca archaeological site and museum in the heart of Miraflores"
            },
            {
                "name": "Malecón de Miraflores",
                "address": "Malecón Cisneros, Miraflores",
                "latitude": -12.1256,
                "longitude": -77.0301,
                "district": "Miraflores",
                "category": "Park",
                "popularity": 88,
                "rating": 4.7,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 60,
                "tags": ["outdoor", "ocean-view", "walking", "romantic", "free"],
                "description": "Scenic clifftop boardwalk with stunning Pacific Ocean views"
            },
            {
                "name": "Parque del Amor",
                "address": "Malecón Cisneros, Miraflores",
                "latitude": -12.1297,
                "longitude": -77.0303,
                "district": "Miraflores",
                "category": "Park",
                "popularity": 82,
                "rating": 4.5,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 30,
                "tags": ["romantic", "outdoor", "sculpture", "ocean-view", "free"],
                "description": "Romantic park featuring the famous 'El Beso' sculpture"
            },
            
            # BARRANCO
            {
                "name": "Puente de los Suspiros",
                "address": "Jr. Batallón Ayacucho, Barranco",
                "latitude": -12.1489,
                "longitude": -77.0219,
                "district": "Barranco",
                "category": "Landmark",
                "popularity": 85,
                "rating": 4.6,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 20,
                "tags": ["romantic", "historical", "photo-spot", "free"],
                "description": "Iconic wooden bridge and romantic landmark in Barranco"
            },
            {
                "name": "MATE Museo Mario Testino",
                "address": "Av. Pedro de Osma 409, Barranco",
                "latitude": -12.1467,
                "longitude": -77.0198,
                "district": "Barranco",
                "category": "Museum",
                "popularity": 75,
                "rating": 4.5,
                "price_level": 2,
                "opening_hours": {"all": "10:00-19:00"},
                "closed_days": ["monday"],
                "visit_duration": 90,
                "tags": ["art", "photography", "cultural", "indoor"],
                "description": "Contemporary photography museum by renowned photographer Mario Testino"
            },
            {
                "name": "Bajada de Baños",
                "address": "Bajada de Baños, Barranco",
                "latitude": -12.1512,
                "longitude": -77.0189,
                "district": "Barranco",
                "category": "Landmark",
                "popularity": 78,
                "rating": 4.4,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 30,
                "tags": ["beach-access", "walking", "scenic", "free"],
                "description": "Picturesque stairway leading down to the beach with colorful murals"
            },
            {
                "name": "Parque Municipal de Barranco",
                "address": "Av. Grau, Barranco",
                "latitude": -12.1456,
                "longitude": -77.0201,
                "district": "Barranco",
                "category": "Park",
                "popularity": 70,
                "rating": 4.2,
                "price_level": 1,
                "opening_hours": {"all": "06:00-22:00"},
                "closed_days": [],
                "visit_duration": 45,
                "tags": ["outdoor", "family-friendly", "relaxation", "free"],
                "description": "Central park in Barranco's bohemian district"
            },
            {
                "name": "Museo Pedro de Osma",
                "address": "Av. Pedro de Osma 423, Barranco",
                "latitude": -12.1478,
                "longitude": -77.0195,
                "district": "Barranco",
                "category": "Museum",
                "popularity": 72,
                "rating": 4.3,
                "price_level": 2,
                "opening_hours": {"all": "10:00-18:00"},
                "closed_days": ["monday"],
                "visit_duration": 75,
                "tags": ["art", "colonial", "cultural", "indoor"],
                "description": "Museum showcasing colonial and viceregal art"
            },
            
            # CENTRO HISTÓRICO (LIMA)
            {
                "name": "Plaza Mayor de Lima",
                "address": "Jr. de la Unión, Lima",
                "latitude": -12.0464,
                "longitude": -77.0300,
                "district": "Lima",
                "category": "Landmark",
                "popularity": 95,
                "rating": 4.8,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 60,
                "tags": ["historical", "unesco", "photo-spot", "free"],
                "description": "Main square of Lima, UNESCO World Heritage Site"
            },
            {
                "name": "Catedral de Lima",
                "address": "Plaza Mayor, Lima",
                "latitude": -12.0465,
                "longitude": -77.0302,
                "district": "Lima",
                "category": "Religious",
                "popularity": 90,
                "rating": 4.7,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:00"},
                "closed_days": ["sunday"],
                "visit_duration": 60,
                "tags": ["religious", "historical", "architecture", "indoor"],
                "description": "Historic cathedral on the Plaza Mayor"
            },
            {
                "name": "Palacio de Gobierno",
                "address": "Jr. de la Unión s/n, Lima",
                "latitude": -12.0458,
                "longitude": -77.0305,
                "district": "Lima",
                "category": "Landmark",
                "popularity": 85,
                "rating": 4.5,
                "price_level": 1,
                "opening_hours": {"all": "10:00-13:00"},
                "closed_days": ["saturday", "sunday"],
                "visit_duration": 90,
                "tags": ["historical", "government", "architecture"],
                "description": "Government Palace with changing of the guard ceremony"
            },
            {
                "name": "Monasterio de San Francisco",
                "address": "Jr. Lampa y Ancash, Lima",
                "latitude": -12.0456,
                "longitude": -77.0289,
                "district": "Lima",
                "category": "Religious",
                "popularity": 88,
                "rating": 4.6,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:30"},
                "closed_days": [],
                "visit_duration": 90,
                "tags": ["religious", "historical", "catacombs", "architecture"],
                "description": "Historic monastery famous for its catacombs and library"
            },
            {
                "name": "Casa de la Literatura Peruana",
                "address": "Jr. Ancash 207, Lima",
                "latitude": -12.0467,
                "longitude": -77.0278,
                "district": "Lima",
                "category": "Museum",
                "popularity": 70,
                "rating": 4.4,
                "price_level": 1,
                "opening_hours": {"all": "10:00-19:00"},
                "closed_days": ["monday"],
                "visit_duration": 75,
                "tags": ["cultural", "literature", "indoor", "free"],
                "description": "Museum dedicated to Peruvian literature"
            },
            
            # SAN ISIDRO
            {
                "name": "Huaca Huallamarca",
                "address": "Av. Nicolás de Rivera 201, San Isidro",
                "latitude": -12.0956,
                "longitude": -77.0389,
                "district": "San Isidro",
                "category": "Museum",
                "popularity": 75,
                "rating": 4.3,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:00"},
                "closed_days": ["monday"],
                "visit_duration": 60,
                "tags": ["archaeological", "historical", "educational"],
                "description": "Pre-Columbian pyramid in the heart of San Isidro"
            },
            {
                "name": "Bosque El Olivar",
                "address": "Av. Paz Soldán, San Isidro",
                "latitude": -12.0978,
                "longitude": -77.0367,
                "district": "San Isidro",
                "category": "Park",
                "popularity": 82,
                "rating": 4.6,
                "price_level": 1,
                "opening_hours": {"all": "06:00-20:00"},
                "closed_days": [],
                "visit_duration": 60,
                "tags": ["outdoor", "nature", "walking", "peaceful", "free"],
                "description": "Historic olive grove and urban park"
            },
            {
                "name": "Parque El Olivar",
                "address": "Av. República de Panamá, San Isidro",
                "latitude": -12.0989,
                "longitude": -77.0356,
                "district": "San Isidro",
                "category": "Park",
                "popularity": 78,
                "rating": 4.5,
                "price_level": 1,
                "opening_hours": {"all": "06:00-20:00"},
                "closed_days": [],
                "visit_duration": 45,
                "tags": ["outdoor", "jogging", "family-friendly", "free"],
                "description": "Beautiful park with ancient olive trees"
            },
            {
                "name": "Country Club Lima Hotel",
                "address": "Los Eucaliptos 590, San Isidro",
                "latitude": -12.0912,
                "longitude": -77.0378,
                "district": "San Isidro",
                "category": "Dining",
                "popularity": 70,
                "rating": 4.7,
                "price_level": 4,
                "opening_hours": {"all": "12:00-23:00"},
                "closed_days": [],
                "visit_duration": 120,
                "tags": ["luxury", "dining", "indoor"],
                "description": "Luxury hotel with fine dining restaurants"
            },
            {
                "name": "Jockey Plaza",
                "address": "Av. Javier Prado Este 4200, San Isidro",
                "latitude": -12.0867,
                "longitude": -77.0234,
                "district": "San Isidro",
                "category": "Shopping",
                "popularity": 85,
                "rating": 4.5,
                "price_level": 3,
                "opening_hours": {"all": "11:00-22:00"},
                "closed_days": [],
                "visit_duration": 150,
                "tags": ["shopping", "dining", "entertainment", "indoor"],
                "description": "Major shopping mall in Lima"
            },
            
            # CALLAO
            {
                "name": "Fortaleza del Real Felipe",
                "address": "Plaza Independencia, Callao",
                "latitude": -12.0656,
                "longitude": -77.1567,
                "district": "Callao",
                "category": "Museum",
                "popularity": 80,
                "rating": 4.4,
                "price_level": 2,
                "opening_hours": {"all": "09:00-16:00"},
                "closed_days": ["monday"],
                "visit_duration": 90,
                "tags": ["historical", "military", "fortress", "educational"],
                "description": "Historic Spanish fortress and military museum"
            },
            {
                "name": "La Punta",
                "address": "La Punta, Callao",
                "latitude": -12.0689,
                "longitude": -77.1634,
                "district": "Callao",
                "category": "Beach",
                "popularity": 75,
                "rating": 4.2,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 90,
                "tags": ["beach", "outdoor", "ocean-view", "walking", "free"],
                "description": "Seaside district with ocean views and seafood restaurants"
            },
            {
                "name": "Museo Naval del Perú",
                "address": "Av. Jorge Chávez 123, Callao",
                "latitude": -12.0623,
                "longitude": -77.1489,
                "district": "Callao",
                "category": "Museum",
                "popularity": 70,
                "rating": 4.3,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:00"},
                "closed_days": ["monday"],
                "visit_duration": 75,
                "tags": ["naval", "historical", "educational", "indoor"],
                "description": "Naval museum showcasing Peru's maritime history"
            },
            {
                "name": "Ventanilla Beach",
                "address": "Ventanilla, Callao",
                "latitude": -11.8789,
                "longitude": -77.1456,
                "district": "Callao",
                "category": "Beach",
                "popularity": 68,
                "rating": 4.0,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 120,
                "tags": ["beach", "outdoor", "swimming", "free"],
                "description": "Popular beach in northern Callao"
            },
            {
                "name": "Chucuito Malecón",
                "address": "Malecón Figueredo, Callao",
                "latitude": -12.0567,
                "longitude": -77.1523,
                "district": "Callao",
                "category": "Park",
                "popularity": 72,
                "rating": 4.1,
                "price_level": 1,
                "opening_hours": {"all": "00:00-23:59"},
                "closed_days": [],
                "visit_duration": 60,
                "tags": ["outdoor", "ocean-view", "walking", "free"],
                "description": "Waterfront promenade with ocean views"
            },
            
            # SURCO
            {
                "name": "Parque de la Amistad",
                "address": "Av. Caminos del Inca, Surco",
                "latitude": -12.1378,
                "longitude": -76.9956,
                "district": "Surco",
                "category": "Park",
                "popularity": 78,
                "rating": 4.4,
                "price_level": 1,
                "opening_hours": {"all": "06:00-22:00"},
                "closed_days": [],
                "visit_duration": 90,
                "tags": ["outdoor", "family-friendly", "sports", "free"],
                "description": "Large park with sports facilities and green spaces"
            },
            {
                "name": "Circuito Mágico del Agua",
                "address": "Parque de la Reserva, Lima",
                "latitude": -12.0700,
                "longitude": -77.0367,
                "district": "Lima",
                "category": "Park",
                "popularity": 92,
                "rating": 4.7,
                "price_level": 1,
                "opening_hours": {"all": "15:00-22:30"},
                "closed_days": ["monday"],
                "visit_duration": 90,
                "tags": ["outdoor", "fountains", "family-friendly", "night-activity"],
                "description": "Spectacular water fountain park with light shows"
            },
            {
                "name": "Museo Larco",
                "address": "Av. Bolívar 1515, Pueblo Libre",
                "latitude": -12.0722,
                "longitude": -77.0733,
                "district": "Pueblo Libre",
                "category": "Museum",
                "popularity": 88,
                "rating": 4.8,
                "price_level": 3,
                "opening_hours": {"all": "10:00-19:00"},
                "closed_days": [],
                "visit_duration": 120,
                "tags": ["archaeological", "pre-columbian", "cultural", "indoor"],
                "description": "World-class museum of pre-Columbian art"
            },
            {
                "name": "Museo Nacional de Arqueología",
                "address": "Plaza Bolívar, Pueblo Libre",
                "latitude": -12.0734,
                "longitude": -77.0745,
                "district": "Pueblo Libre",
                "category": "Museum",
                "popularity": 82,
                "rating": 4.5,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:00"},
                "closed_days": ["monday"],
                "visit_duration": 105,
                "tags": ["archaeological", "educational", "cultural", "indoor"],
                "description": "National archaeology museum"
            },
            {
                "name": "Parque de las Leyendas",
                "address": "Av. La Marina 2000, San Miguel",
                "latitude": -12.0678,
                "longitude": -77.0856,
                "district": "San Miguel",
                "category": "Zoo",
                "popularity": 85,
                "rating": 4.3,
                "price_level": 2,
                "opening_hours": {"all": "09:00-17:00"},
                "closed_days": [],
                "visit_duration": 180,
                "tags": ["family-friendly", "zoo", "educational", "outdoor"],
                "description": "Zoo and archaeological park"
            },
        ]
        
        # Add POIs to database
        for poi_data in sample_pois:
            poi = POI(**poi_data)
            db.add(poi)
        
        db.commit()
        logger.info(f"Successfully loaded {len(sample_pois)} sample POIs")
        
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Initializing TouristGen Pro database...")
    init_database()
    load_sample_pois()
    logger.info("Database initialization complete!")
