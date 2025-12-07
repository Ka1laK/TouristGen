import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.database import engine, Base
# Import all models to ensure they are registered with Base metadata
from app.models import poi, user, feedback

def init_db():
    print("Initializing database tables on Supabase...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
        return True
    except Exception as e:
        print("Error creating tables:")
        print(e)
        return False

if __name__ == "__main__":
    if init_db():
        sys.exit(0)
    else:
        sys.exit(1)
