"""
Unit Tests for CarbonFetcher
=============================
Tests carbon intensity fetching and region selection logic.

Test Coverage:
- test_greenest_region_selection: Verify correct selection of lowest carbon region
- test_fetch_carbon_handles_400: Test error handling for HTTP 400 responses
"""

import pytest
import requests
import requests_mock
from carbon_fetcher import CarbonFetcher


def test_greenest_region_selection():
    """
    Test that get_greenest_region() correctly identifies the region 
    with the lowest carbon intensity from multiple regions.
    
    Mocks API responses for IN, FI, DE with different carbon intensities:
    - IN: 650 gCO₂/kWh
    - FI: 45 gCO₂/kWh (lowest - should be selected)
    - DE: 420 gCO₂/kWh
    
    Asserts that Finland (FI) is selected as the greenest region.
    """
    # Initialize CarbonFetcher
    fetcher = CarbonFetcher(api_key="test-api-key-12345")
    
    # Create mock API responses
    with requests_mock.Mocker() as mock:
        # Mock India response (high carbon)
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=IN",
            json={
                "zone": "IN",
                "carbonIntensity": 650,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # Mock Finland response (low carbon - greenest)
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=FI",
            json={
                "zone": "FI",
                "carbonIntensity": 45,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # Mock Germany response (medium carbon)
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=DE",
            json={
                "zone": "DE",
                "carbonIntensity": 420,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # Mock Japan response
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=JP",
            json={
                "zone": "JP",
                "carbonIntensity": 512,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # Mock Australia response
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=AU-NSW",
            json={
                "zone": "AU-NSW",
                "carbonIntensity": 738,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # Mock Brazil response
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=BR-CS",
            json={
                "zone": "BR-CS",
                "carbonIntensity": 178,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # Call get_greenest_region()
        result = fetcher.get_greenest_region()
        
        # Assertions
        assert result is not None, "get_greenest_region() should return a result"
        assert result['zone'] == 'FI', "Finland should be selected as greenest region"
        assert result['carbonIntensity'] == 45, "Carbon intensity should be 45 gCO₂/kWh"
        assert result['name'] == 'Finland', "Region name should be Finland"
        assert 'savings' in result, "Result should include carbon savings calculation"
        assert result['totalRegions'] == 6, "Should have data from all 6 regions"


def test_fetch_carbon_handles_400():
    """
    Test that fetch_carbon_intensity() properly handles HTTP 400 Bad Request errors.
    
    Mocks the ElectricityMap API to return a 400 status code,
    which indicates an invalid request (e.g., bad zone code).
    
    Asserts that:
    - Function returns None (indicating failure)
    - No exception is raised (error handled gracefully)
    """
    # Initialize CarbonFetcher
    fetcher = CarbonFetcher(api_key="test-api-key-12345")
    
    # Mock API to return 400 Bad Request
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=INVALID",
            json={"error": "Invalid zone code"},
            status_code=400
        )
        
        # Call fetch_carbon_intensity with invalid zone
        result = fetcher.fetch_carbon_intensity("INVALID", use_cache=False)
        
        # Assertions
        assert result is None, "fetch_carbon_intensity should return None on 400 error"
        
        # Verify the mock was called
        assert mock.called, "API endpoint should have been called"
        assert mock.call_count == 1, "API should be called exactly once"


def test_fetch_carbon_success():
    """
    Test successful carbon intensity fetch for a single region.
    Verifies data structure and caching behavior.
    """
    fetcher = CarbonFetcher(api_key="test-api-key")
    
    with requests_mock.Mocker() as mock:
        # Mock successful API response
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=DE",
            json={
                "zone": "DE",
                "carbonIntensity": 420,
                "datetime": "2025-01-15T10:30:00Z",
                "updatedAt": "2025-01-15T10:35:00Z"
            },
            status_code=200
        )
        
        # First call - should hit API
        result1 = fetcher.fetch_carbon_intensity("DE", use_cache=False)
        
        assert result1 is not None
        assert result1['zone'] == 'DE'
        assert result1['carbonIntensity'] == 420
        assert 'datetime' in result1
        
        # Second call with cache - should use cached data
        result2 = fetcher.fetch_carbon_intensity("DE", use_cache=True)
        
        assert result2 is not None
        assert result2['carbonIntensity'] == 420
        
        # API should only be called once (second call used cache)
        assert mock.call_count == 1, "API should only be called once due to caching"


def test_fetch_carbon_handles_401():
    """Test handling of authentication errors (401 Unauthorized)."""
    fetcher = CarbonFetcher(api_key="invalid-key")
    
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=IN",
            json={"error": "Unauthorized"},
            status_code=401
        )
        
        result = fetcher.fetch_carbon_intensity("IN", use_cache=False)
        
        assert result is None, "Should return None on 401 authentication error"
        assert mock.called


def test_fetch_carbon_handles_429():
    """Test handling of rate limit errors (429 Too Many Requests)."""
    fetcher = CarbonFetcher(api_key="test-key")
    
    with requests_mock.Mocker() as mock:
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=FI",
            json={"error": "Rate limit exceeded"},
            status_code=429
        )
        
        result = fetcher.fetch_carbon_intensity("FI", use_cache=False)
        
        assert result is None, "Should return None on 429 rate limit error"
        assert mock.called


def test_fetch_carbon_handles_timeout():
    """Test handling of network timeout errors."""
    fetcher = CarbonFetcher(api_key="test-key")
    
    with requests_mock.Mocker() as mock:
        # Mock timeout exception
        mock.get(
            "https://api.electricitymap.org/v3/carbon-intensity/latest?zone=JP",
            exc=requests.exceptions.Timeout
        )
        
        result = fetcher.fetch_carbon_intensity("JP", use_cache=False)
        
        assert result is None, "Should return None on timeout"
        assert mock.called
