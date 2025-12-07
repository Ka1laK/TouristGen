import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from sqlalchemy import text
from app.database import engine

def test_connection():
    try:
        print("Testing connection to:", engine.url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful! Result:", result.fetchone())
            return True
    except Exception as e:
        print("Connection failed!")
        print(e)
        return False

if __name__ == "__main__":
    if test_connection():
        sys.exit(0)
    else:
        sys.exit(1)
