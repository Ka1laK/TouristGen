import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class ScraperService:
    """
    Web scraper for POI data
    
    NOTE: This is a basic implementation. For production:
    - Respect robots.txt
    - Implement proper rate limiting
    - Handle errors gracefully
    - Consider using Playwright for JavaScript-heavy sites
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TouristGen Educational Project (respectful crawler)'
        })
        self.rate_limit = settings.scraper_rate_limit
        self.timeout = settings.scraper_timeout
        self.last_request_time = 0
    
    def _rate_limit_wait(self):
        """Ensure rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        
        self.last_request_time = time.time()
    
    def scrape_wikipedia_poi(self, poi_name: str, district: str = "") -> Optional[Dict]:
        """
        Scrape POI information from Wikipedia
        
        Returns basic information if found
        """
        try:
            self._rate_limit_wait()
            
            # Search Wikipedia
            search_url = "https://es.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": f"{poi_name} {district} Lima",
                "format": "json"
            }
            
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if "query" not in data or "search" not in data["query"]:
                return None
            
            results = data["query"]["search"]
            
            if not results:
                return None
            
            # Get first result
            page_title = results[0]["title"]
            snippet = results[0]["snippet"]
            
            # Clean HTML from snippet
            snippet_clean = BeautifulSoup(snippet, "html.parser").get_text()
            
            return {
                "name": page_title,
                "description": snippet_clean,
                "source": "Wikipedia"
            }
            
        except Exception as e:
            logger.error(f"Error scraping Wikipedia for {poi_name}: {e}")
            return None
    
    def scrape_google_places_info(self, poi_name: str, district: str = "") -> Optional[Dict]:
        """
        Placeholder for Google Places scraping
        
        NOTE: Google Places requires API key and has usage limits
        This is a placeholder - actual implementation would use Google Places API
        """
        logger.warning("Google Places scraping not implemented - requires API key")
        return None
    
    def get_poi_coordinates(self, address: str) -> Optional[Dict]:
        """
        Get coordinates using Nominatim (OpenStreetMap)
        Free geocoding service - no API key required
        """
        try:
            self._rate_limit_wait()
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": f"{address}, Lima, Peru",
                "format": "json",
                "limit": 1
            }
            
            headers = {
                "User-Agent": "TouristGen/1.0 (Educational Project)"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return None
            
            result = data[0]
            
            return {
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
                "display_name": result.get("display_name", "")
            }
            
        except Exception as e:
            logger.error(f"Error geocoding {address}: {e}")
            return None
    
    def scrape_municipal_tourism_data(self, district: str) -> List[Dict]:
        """
        Placeholder for scraping municipal tourism websites
        
        Each district may have different website structure
        This would need custom implementation per source
        """
        logger.info(f"Municipal scraping for {district} not implemented")
        return []
    
    def enrich_poi_data(self, poi_data: Dict) -> Dict:
        """
        Enrich POI data with scraped information
        
        Args:
            poi_data: Basic POI data with at least 'name' and 'district'
        
        Returns:
            Enriched POI data
        """
        enriched = poi_data.copy()
        
        # Try to get Wikipedia info
        wiki_info = self.scrape_wikipedia_poi(
            poi_data.get("name", ""),
            poi_data.get("district", "")
        )
        
        if wiki_info:
            if not enriched.get("description"):
                enriched["description"] = wiki_info.get("description", "")
        
        # Try to geocode if no coordinates
        if not enriched.get("latitude") or not enriched.get("longitude"):
            if enriched.get("address"):
                coords = self.get_poi_coordinates(enriched["address"])
                
                if coords:
                    enriched["latitude"] = coords["latitude"]
                    enriched["longitude"] = coords["longitude"]
        
        return enriched
    
    def batch_enrich_pois(self, pois: List[Dict]) -> List[Dict]:
        """
        Enrich multiple POIs with rate limiting
        
        This is slow due to rate limiting - use sparingly
        """
        enriched_pois = []
        
        for i, poi in enumerate(pois):
            logger.info(f"Enriching POI {i+1}/{len(pois)}: {poi.get('name', 'Unknown')}")
            
            enriched = self.enrich_poi_data(poi)
            enriched_pois.append(enriched)
            
            # Extra delay between POIs
            if i < len(pois) - 1:
                time.sleep(2)
        
        return enriched_pois
