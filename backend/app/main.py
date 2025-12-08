from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import pois, optimizer, weather, routes, quick_optimizer, geocoding
from app.chatbot import api as chatbot_api
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create database tables
logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="TouristGen Pro API",
    description="Intelligent Tourist Route Planner for Lima and Callao using Genetic Algorithms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pois.router, prefix="/api/pois", tags=["POIs"])
app.include_router(optimizer.router, prefix="/api/optimize", tags=["Optimizer"])
app.include_router(quick_optimizer.router, prefix="/api/optimize", tags=["Quick Optimizer"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather"])
app.include_router(routes.router, prefix="/api/routes", tags=["Routes"])
app.include_router(geocoding.router, prefix="/api/geocoding", tags=["Geocoding"])
app.include_router(chatbot_api.router, prefix="/api/chat", tags=["Chatbot"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "TouristGen Pro API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
