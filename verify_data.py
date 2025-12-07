import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from sqlalchemy import text
from app.database import engine

def verify_data():
    print("--- VERIFICACIÓN DE DATOS (SUPABASE) ---")
    try:
        with engine.connect() as connection:
            # Count total
            result = connection.execute(text("SELECT COUNT(*) FROM pois WHERE is_active = true"))
            count = result.scalar()
            print(f"Total POIs Activos: {count}")
            
            # Show sample
            print("\nTop 5 POIs (San Miguel):")
            rows = connection.execute(text("SELECT name, category, rating FROM pois WHERE district = 'San Miguel' ORDER BY popularity DESC LIMIT 5"))
            for row in rows:
                print(f"- {row[0]} ({row[1]}) - Rating: {row[2]}")
                
            return True
    except Exception as e:
        print("Error verificando datos:")
        print(e)
        return False

if __name__ == "__main__":
    verify_data()
