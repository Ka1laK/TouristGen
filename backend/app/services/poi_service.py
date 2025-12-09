from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.models.poi import POI
from app.models.feedback import Feedback
import logging

logger = logging.getLogger(__name__)


class POIService:
    """Service for managing Points of Interest"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_pois(self, active_only: bool = True) -> List[POI]:
        """Get all POIs"""
        query = self.db.query(POI)
        if active_only:
            query = query.filter(POI.is_active == True)
        return query.all()
    
    def get_poi_by_id(self, poi_id: int) -> Optional[POI]:
        """Get POI by ID"""
        return self.db.query(POI).filter(POI.id == poi_id).first()
    
    def get_pois_by_district(self, district: str) -> List[POI]:
        """Get all POIs in a district"""
        return self.db.query(POI).filter(
            POI.district == district,
            POI.is_active == True
        ).all()
    
    def get_pois_by_category(self, category: str) -> List[POI]:
        """Get all POIs of a category"""
        return self.db.query(POI).filter(
            POI.category == category,
            POI.is_active == True
        ).all()
    
    def get_pois_by_tags(self, tags: List[str]) -> List[POI]:
        """Get POIs that have any of the specified tags"""
        pois = self.get_all_pois()
        
        matching_pois = []
        for poi in pois:
            if poi.tags and any(tag in poi.tags for tag in tags):
                matching_pois.append(poi)
        
        return matching_pois
    
    def filter_pois(
        self,
        districts: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        max_price_level: Optional[int] = None
    ) -> List[POI]:
        """Filter POIs by multiple criteria"""
        query = self.db.query(POI).filter(POI.is_active == True)
        
        if districts:
            query = query.filter(POI.district.in_(districts))
        
        if categories:
            query = query.filter(POI.category.in_(categories))
        
        if min_rating is not None:
            query = query.filter(POI.rating >= min_rating)
        
        if max_price_level is not None:
            query = query.filter(POI.price_level <= max_price_level)
        
        pois = query.all()
        
        # Filter by tags (can't do in SQL easily with JSON)
        if tags:
            pois = [
                poi for poi in pois
                if poi.tags and any(tag in poi.tags for tag in tags)
            ]
        
        return pois
    
    def create_poi(self, poi_data: Dict) -> POI:
        """Create a new POI"""
        poi = POI(**poi_data)
        self.db.add(poi)
        self.db.commit()
        self.db.refresh(poi)
        return poi
    
    def update_poi(self, poi_id: int, poi_data: Dict) -> Optional[POI]:
        """Update a POI"""
        poi = self.get_poi_by_id(poi_id)
        if not poi:
            return None
        
        for key, value in poi_data.items():
            if hasattr(poi, key):
                setattr(poi, key, value)
        
        self.db.commit()
        self.db.refresh(poi)
        return poi
    
    def delete_poi(self, poi_id: int) -> bool:
        """Soft delete a POI"""
        poi = self.get_poi_by_id(poi_id)
        if not poi:
            return False
        
        poi.is_active = False
        self.db.commit()
        return True
    
    def update_learned_weights(self):
        """
        Update learned popularity weights based on user feedback
        
        This implements the learning mechanism:
        - POIs with high ratings get boosted
        - POIs that are frequently skipped get reduced
        """
        pois = self.get_all_pois()
        
        for poi in pois:
            # Get feedback for this POI
            feedbacks = self.db.query(Feedback).filter(
                Feedback.poi_id == poi.id
            ).all()
            
            if not feedbacks:
                continue
            
            # Calculate average rating
            ratings = [f.rating for f in feedbacks if f.rating is not None]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                
                # Adjust learned weight based on rating
                # Rating 5 -> weight 1.3
                # Rating 3 -> weight 1.0
                # Rating 1 -> weight 0.7
                poi.learned_popularity = 0.7 + (avg_rating / 5.0) * 0.6
            
            # Check visit rate
            total_feedback = len(feedbacks)
            visited = sum(1 for f in feedbacks if f.visited == 1)
            
            if total_feedback > 0:
                visit_rate = visited / total_feedback
                
                # Adjust weight based on visit rate
                # High visit rate -> boost
                # Low visit rate -> reduce
                if visit_rate > 0.8:
                    poi.learned_popularity *= 1.2
                elif visit_rate < 0.3:
                    poi.learned_popularity *= 0.8
        
        self.db.commit()
        logger.info("Updated learned weights for all POIs")
    
    def get_popular_pois(self, limit: int = 10) -> List[POI]:
        """Get most popular POIs"""
        return self.db.query(POI).filter(
            POI.is_active == True
        ).order_by(
            POI.popularity.desc()
        ).limit(limit).all()
    
    def get_top_rated_pois(self, limit: int = 10) -> List[POI]:
        """Get top rated POIs"""
        return self.db.query(POI).filter(
            POI.is_active == True,
            POI.rating > 0
        ).order_by(
            POI.rating.desc()
        ).limit(limit).all()
    
    def get_districts(self) -> List[str]:
        """Get list of all districts"""
        districts = self.db.query(POI.district).distinct().all()
        return [d[0] for d in districts]
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        categories = self.db.query(POI.category).distinct().all()
        return [c[0] for c in categories]
    
    def get_poi_count_by_district(self) -> Dict[str, int]:
        """Get count of POIs per district"""
        from sqlalchemy import func
        
        results = self.db.query(
            POI.district,
            func.count(POI.id)
        ).filter(
            POI.is_active == True
        ).group_by(POI.district).all()
        
        return {district: count for district, count in results}

    def count_pois_near(self, lat: float, lon: float, radius_km: float = 2.0) -> int:
        """
        Count active POIs within a rough radius of coordinates.
        Uses simple box approximation for speed (1 deg lat ~= 111km).
        """
        # Roughly: 1km ~= 0.009 degrees latitude
        deg_radius = radius_km / 111.0
        
        # Simple bounding box query
        count = self.db.query(POI).filter(
            POI.is_active == True,
            POI.latitude.between(lat - deg_radius, lat + deg_radius),
            POI.longitude.between(lon - deg_radius, lon + deg_radius)
        ).count()
        
        return count

    def search_by_name(self, name: str, limit: int = 5) -> List[POI]:
        """
        Search POIs by name using fuzzy matching (LIKE).
        Used for district inference from place references.
        
        Args:
            name: Place name to search for
            limit: Maximum number of results
            
        Returns:
            List of matching POIs ordered by relevance (rating)
        """
        # Use ILIKE-style matching (case insensitive)
        search_pattern = f"%{name}%"
        
        return self.db.query(POI).filter(
            POI.is_active == True,
            POI.name.ilike(search_pattern)
        ).order_by(
            POI.rating.desc()
        ).limit(limit).all()
