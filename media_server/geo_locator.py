"""
GeoLocator module for finding nearest cities based on coordinates.
"""
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CityEntry:
    """Data class for storing city information."""
    city: str
    latitude: float
    longitude: float
    country: str


class GeoLocator:
    """Class for finding nearest cities based on geographic coordinates."""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize GeoLocator with city data.
        
        Args:
            csv_path: Optional path to CSV file. If not provided, uses bundled resource.
        """
        self.cities: List[CityEntry] = []
        self._load_cities(csv_path)
    
    def _load_cities(self, csv_path: Optional[str] = None) -> None:
        """
        Load city data from CSV file.
        
        Args:
            csv_path: Path to CSV file. If None, uses bundled resource.
        """
        if csv_path is None:
            # Use bundled resource
            csv_path = Path(__file__).parent / "data" / "cities.csv"
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        # Check if all required fields are present and not None
                        if all(key in row and row[key] is not None for key in ['city', 'lat', 'lng', 'country']):
                            city_entry = CityEntry(
                                city=row['city'],
                                latitude=float(row['lat']),
                                longitude=float(row['lng']),
                                country=row['country']
                            )
                            self.cities.append(city_entry)
                        else:
                            print(f"Warning: Skipping entry with missing fields: {row}")
                    except (KeyError, ValueError, TypeError) as e:
                        # Skip invalid entries
                        print(f"Warning: Skipping invalid entry: {row}. Error: {e}")
        except FileNotFoundError:
            print(f"Warning: CSV file not found at {csv_path}. Using empty city list.")
    
    def nearest_city(self, latitude: float, longitude: float) -> Optional[CityEntry]:
        """
        Find the nearest city to the given coordinates.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            CityEntry of the nearest city, or None if no cities are loaded.
        """
        if not self.cities:
            return None
        
        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """
            Calculate the great circle distance between two points on Earth.
            
            Args:
                lat1, lon1: First point coordinates
                lat2, lon2: Second point coordinates
                
            Returns:
                Distance in kilometers
            """
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in kilometers
            radius = 6371
            
            return radius * c
        
        # Find the city with minimum distance
        nearest = min(
            self.cities,
            key=lambda city: haversine_distance(latitude, longitude, city.latitude, city.longitude)
        )
        
        return nearest