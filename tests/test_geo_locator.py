"""
Tests for the GeoLocator module.
"""
import pytest
import tempfile
import os
from pathlib import Path
from media_server.geo_locator import GeoLocator, CityEntry


class TestCityEntry:
    """Test the CityEntry data class."""
    
    def test_city_entry_creation(self):
        """Test creating a CityEntry instance."""
        city = CityEntry(
            city="New York",
            latitude=40.7128,
            longitude=-74.0060,
            country="USA"
        )
        assert city.city == "New York"
        assert city.latitude == 40.7128
        assert city.longitude == -74.0060
        assert city.country == "USA"
    
    def test_city_entry_equality(self):
        """Test CityEntry equality comparison."""
        city1 = CityEntry("Paris", 48.8566, 2.3522, "France")
        city2 = CityEntry("Paris", 48.8566, 2.3522, "France")
        city3 = CityEntry("London", 51.5074, -0.1278, "UK")
        
        assert city1 == city2
        assert city1 != city3


class TestGeoLocator:
    """Test the GeoLocator class."""
    
    @pytest.fixture
    def temp_csv_file(self):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("city,lat,lng,country\n")
            f.write("New York,40.7128,-74.0060,USA\n")
            f.write("London,51.5074,-0.1278,UK\n")
            f.write("Tokyo,35.6762,139.6503,Japan\n")
            f.write("Sydney,-33.8688,151.2093,Australia\n")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def invalid_csv_file(self):
        """Create a CSV file with invalid data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("city,lat,lng,country\n")
            f.write("Valid City,40.7128,-74.0060,USA\n")
            f.write("Invalid Lat,not_a_number,-74.0060,USA\n")
            f.write("Missing Field,40.7128\n")
            f.write("Another Valid,-33.8688,151.2093,Australia\n")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_load_from_custom_csv(self, temp_csv_file):
        """Test loading cities from a custom CSV file."""
        locator = GeoLocator(temp_csv_file)
        
        assert len(locator.cities) == 4
        assert locator.cities[0].city == "New York"
        assert locator.cities[1].city == "London"
        assert locator.cities[2].city == "Tokyo"
        assert locator.cities[3].city == "Sydney"
    
    def test_load_from_bundled_csv(self):
        """Test loading cities from the bundled CSV resource."""
        # This test will work if the bundled CSV exists
        locator = GeoLocator()
        
        # The bundled CSV should have 25 cities
        if locator.cities:  # Only test if file exists
            assert len(locator.cities) == 25
            # Check a few known cities
            city_names = [city.city for city in locator.cities]
            assert "New York" in city_names
            assert "London" in city_names
            assert "Tokyo" in city_names
    
    def test_load_nonexistent_file(self):
        """Test handling of non-existent CSV file."""
        locator = GeoLocator("/path/to/nonexistent/file.csv")
        assert len(locator.cities) == 0
    
    def test_load_invalid_data(self, invalid_csv_file):
        """Test handling of invalid data in CSV file."""
        locator = GeoLocator(invalid_csv_file)
        
        # Should only load valid entries
        assert len(locator.cities) == 2
        assert locator.cities[0].city == "Valid City"
        assert locator.cities[1].city == "Another Valid"
    
    def test_nearest_city_basic(self, temp_csv_file):
        """Test finding the nearest city."""
        locator = GeoLocator(temp_csv_file)
        
        # Test point near New York
        nearest = locator.nearest_city(40.7, -74.0)
        assert nearest.city == "New York"
        
        # Test point near London
        nearest = locator.nearest_city(51.5, 0.0)
        assert nearest.city == "London"
        
        # Test point near Tokyo
        nearest = locator.nearest_city(35.0, 140.0)
        assert nearest.city == "Tokyo"
        
        # Test point near Sydney
        nearest = locator.nearest_city(-34.0, 151.0)
        assert nearest.city == "Sydney"
    
    def test_nearest_city_exact_match(self, temp_csv_file):
        """Test finding nearest city when coordinates exactly match."""
        locator = GeoLocator(temp_csv_file)
        
        # Exact London coordinates
        nearest = locator.nearest_city(51.5074, -0.1278)
        assert nearest.city == "London"
        assert nearest.latitude == 51.5074
        assert nearest.longitude == -0.1278
    
    def test_nearest_city_equidistant(self):
        """Test nearest city behavior with equidistant points."""
        # Create a CSV with two cities at same distance from a point
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("city,lat,lng,country\n")
            f.write("City A,0.0,0.0,Country A\n")
            f.write("City B,0.0,2.0,Country B\n")
            temp_path = f.name
        
        try:
            locator = GeoLocator(temp_path)
            
            # Point at (0, 1) is equidistant from both cities
            nearest = locator.nearest_city(0.0, 1.0)
            
            # Should return one of them (implementation dependent)
            assert nearest.city in ["City A", "City B"]
        finally:
            os.unlink(temp_path)
    
    def test_nearest_city_empty_list(self):
        """Test nearest_city with no cities loaded."""
        locator = GeoLocator("/nonexistent/file.csv")
        
        nearest = locator.nearest_city(40.7128, -74.0060)
        assert nearest is None
    
    def test_nearest_city_antipodal_points(self, temp_csv_file):
        """Test nearest city with antipodal points (opposite sides of Earth)."""
        locator = GeoLocator(temp_csv_file)
        
        # Point roughly antipodal to New York (in Indian Ocean)
        nearest = locator.nearest_city(-40.7128, 105.9940)
        
        # Should find Sydney as nearest (southern hemisphere)
        assert nearest.city == "Sydney"
    
    def test_nearest_city_poles(self, temp_csv_file):
        """Test nearest city from North and South poles."""
        locator = GeoLocator(temp_csv_file)
        
        # North Pole
        nearest = locator.nearest_city(90.0, 0.0)
        # London should be nearest to North Pole among test cities
        assert nearest.city == "London"
        
        # South Pole
        nearest = locator.nearest_city(-90.0, 0.0)
        # Sydney should be nearest to South Pole among test cities
        assert nearest.city == "Sydney"
    
    def test_nearest_city_wraparound(self, temp_csv_file):
        """Test nearest city with longitude wraparound."""
        locator = GeoLocator(temp_csv_file)
        
        # Point near Tokyo but with longitude > 180
        # This tests if the haversine formula handles wraparound correctly
        nearest = locator.nearest_city(35.6762, 139.6503 + 360)
        assert nearest.city == "Tokyo"
    
    def test_large_dataset_performance(self):
        """Test performance with a larger dataset."""
        # Create a larger CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("city,lat,lng,country\n")
            
            # Generate 1000 cities in a grid pattern
            for i in range(100):
                for j in range(10):
                    lat = -80 + (i * 1.6)  # From -80 to +80
                    lng = -180 + (j * 36)  # From -180 to +180
                    f.write(f"City_{i}_{j},{lat},{lng},Country\n")
            
            temp_path = f.name
        
        try:
            locator = GeoLocator(temp_path)
            assert len(locator.cities) == 1000
            
            # Test finding nearest city should complete quickly
            import time
            start = time.time()
            nearest = locator.nearest_city(0.0, 0.0)
            end = time.time()
            
            assert nearest is not None
            # Should complete in less than 0.1 seconds even with 1000 cities
            assert (end - start) < 0.1
        finally:
            os.unlink(temp_path)