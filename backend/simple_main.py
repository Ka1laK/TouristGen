import uvicorn
import os
import sys

# Add the current directory to the path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    print("Starting TouristGen Pro (Full Version)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
