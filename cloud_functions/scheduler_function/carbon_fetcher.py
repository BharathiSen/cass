"""
Carbon Intensity Fetcher Module
---------------------------------
Fetches real-time carbon intensity data from ElectricityMap API.

Supports multiple regions: India (IN), Finland (FI), California (US-CA).
Includes caching, retry logic, and error handling.
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class CarbonFetcher:
    """
    Fetches carbon intensity data from ElectricityMap API.

    Attributes:
        api_key (str): ElectricityMap API key
        base_url (str): API endpoint base URL
        cache (dict): In-memory cache for API responses
        cache_ttl (int): Cache time-to-live in seconds (default: 300s = 5min)
    """

    def __init__(self, api_key: str, cache_ttl: int = 300):
        """
        Initialize the Carbon Fetcher.

        Args:
            api_key: gwASf8vJiQ92CPIuRzuy
            cache_ttl: Cache duration in seconds (default: 5 minutes)
        """
        self.api_key = api_key
        self.base_url = "https://api.electricitymap.org/v3/carbon-intensity/latest"
        self.cache = {}
        self.cache_ttl = cache_ttl

        # Define supported regions (6 working zones with flags)
        self.regions = {
            "IN": {"name": "India", "flag": ""},
            "FI": {"name": "Finland", "flag": ""},
            "DE": {"name": "Germany", "flag": ""},
            "JP": {"name": "Japan", "flag": ""},
            "AU-NSW": {"name": "New South Wales, Australia", "flag": ""},
            "BR-CS": {"name": "Central-South Brazil", "flag": ""}
        }

    def fetch_carbon_intensity(self, zone: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Fetch carbon intensity for a specific zone.

        Args:
            zone: Region code (e.g., 'IN', 'FI', 'US-CA')
            use_cache: Whether to use cached data (default: True)

        Returns:
            Dict with carbon intensity data or None if fetch fails
            {
                'zone': 'IN',
                'carbonIntensity': 650,
                'datetime': '2025-11-05T10:30:00Z',
                'updatedAt': '2025-11-05T10:35:00Z'
            }
        """
        # Check cache first
        if use_cache and zone in self.cache:
            cached_data, timestamp = self.cache[zone]
            if time.time() - timestamp < self.cache_ttl:
                print(f"✓ Using cached data for {zone}")
                return cached_data

        # Fetch fresh data from API
        try:
            print(f"⟳ Fetching live carbon data for {zone}...")

            headers = {
                "auth-token": self.api_key
            }
            params = {
                "zone": zone
            }

            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )

            # Check if request was successful
            if response.status_code == 200:
                data = response.json()

                # Cache the result
                self.cache[zone] = (data, time.time())

                print(f"✓ {zone}: {data.get('carbonIntensity', 'N/A')} gCO₂/kWh")
                return data

            elif response.status_code == 401:
                print(f"✗ Authentication failed. Check your API key.")
                return None

            elif response.status_code == 429:
                print(f"✗ Rate limit exceeded. Try again later.")
                return None

            else:
                print(f"✗ API error for {zone}: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            print(f"✗ Request timeout for {zone}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"✗ Network error for {zone}: {e}")
            return None

        except Exception as e:
            print(f"✗ Unexpected error for {zone}: {e}")
            return None

    def fetch_all_regions(self, display_details: bool = True) -> Dict[str, Optional[Dict]]:
        """
        Fetch carbon intensity for all configured regions.

        Args:
            display_details: Show detailed output with timestamps (default: True)

        Returns:
            Dictionary mapping zone codes to their carbon data
            {
                'IN': {...data...},
                'FI': {...data...},
                'US-CA': {...data...},
                'DE': {...data...},
                'JP': {...data...},
                'AU-NSW': {...data...}
            }
        """
        results = {}

        print(f"\n{'='*70}")
        print(f" FETCHING CARBON INTENSITY DATA FROM {len(self.regions)} REGIONS")
        print(f"{'='*70}")

        for i, zone in enumerate(self.regions.keys(), 1):
            results[zone] = self.fetch_carbon_intensity(zone)
            time.sleep(0.5)  # Small delay to avoid rate limiting

        # Display detailed results table with colorized output
        if display_details:
            print(f"\n{'='*75}")
            print(f" CARBON INTENSITY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*75}")
            print(f"{'Region':<38} {'Carbon':<18} {'Time':<10}")
            print(f"{'-'*75}")

            for zone, data in results.items():
                region_info = self.regions[zone]
                flag = region_info['flag']
                region_name = region_info['name']
                display_name = f"{flag} {zone:8s} - {region_name}"

                if data and 'carbonIntensity' in data:
                    carbon = data['carbonIntensity']
                    timestamp = data.get('datetime', 'N/A')
                    # Format timestamp if available
                    if timestamp != 'N/A' and 'T' in timestamp:
                        try:
                            timestamp = timestamp.split('T')[1].split('.')[0][:5]  # Get HH:MM
                        except:
                            timestamp = 'N/A'

                    carbon_display = f"{carbon:>4} gCO₂/kWh"
                    status = f"✓ {timestamp}"
                    print(f"{display_name:<38} {carbon_display:<18} {status}")
                else:
                    print(f"{display_name:<38} {'N/A':<18} ✗ Failed")

            print(f"{'='*75}\n")

        return results

    def get_greenest_region(self) -> Optional[Dict]:
        """
        Find the region with the lowest carbon intensity.

        Returns:
            Dict with greenest region info or None if all fetches failed
            {
                'zone': 'FI',
                'name': 'Finland',
                'carbonIntensity': 45,
                'datetime': '2025-11-05T10:30:00Z',
                'savings': 461  # gCO₂/kWh saved vs average
            }
        """
        all_data = self.fetch_all_regions(display_details=True)

        # Filter out failed fetches
        valid_regions = {
            zone: data
            for zone, data in all_data.items()
            if data is not None and 'carbonIntensity' in data
        }

        if not valid_regions:
            print("\n✗ No valid carbon data available")
            return None

        # Find region with minimum carbon intensity
        greenest_zone = min(
            valid_regions.keys(),
            key=lambda z: valid_regions[z]['carbonIntensity']
        )

        greenest_data = valid_regions[greenest_zone]

        # Calculate average carbon intensity
        avg_carbon = sum(d['carbonIntensity'] for d in valid_regions.values()) / len(valid_regions)

        # Calculate savings
        savings = round(avg_carbon - greenest_data['carbonIntensity'])

        result = {
            'zone': greenest_zone,
            'name': self.regions[greenest_zone],
            'carbonIntensity': greenest_data['carbonIntensity'],
            'datetime': greenest_data.get('datetime', 'N/A'),
            'updatedAt': greenest_data.get('updatedAt', 'N/A'),
            'savings': savings,
            'totalRegions': len(valid_regions)
        }

        # Update result with region info
        region_info = self.regions[greenest_zone]
        result['name'] = region_info['name']
        result['flag'] = region_info['flag']
        result['averageCarbon'] = round(avg_carbon)

        # Display recommendation with colorized output
        print(f"\n{'='*75}")
        print(f" DEPLOYMENT RECOMMENDATION")
        print(f"{'='*75}")
        print(f" Recommended Region: {result['flag']} {result['name']} ({result['zone']})")
        print(f" Carbon Intensity: {result['carbonIntensity']} gCO₂/kWh")
        print(f" Savings vs Average: {savings} gCO₂/kWh ({round((savings/avg_carbon)*100, 1)}% reduction)")
        print(f" Compared across {len(valid_regions)} regions (avg: {round(avg_carbon)} gCO₂/kWh)")

        # Show failed regions if any
        failed_count = len(self.regions) - len(valid_regions)
        if failed_count > 0:
            print(f"  Note: {failed_count} region(s) failed to fetch data")

        print(f"{'='*75}\n")

        return result

    def compare_regions(self) -> List[Dict]:
        """
        Get all regions sorted by carbon intensity (lowest first).

        Returns:
            List of dicts sorted by carbon intensity
        """
        all_data = self.fetch_all_regions()

        # Build comparison list
        comparison = []
        for zone, data in all_data.items():
            if data and 'carbonIntensity' in data:
                region_info = self.regions[zone]
                comparison.append({
                    'zone': zone,
                    'name': region_info['name'],
                    'flag': region_info['flag'],
                    'carbonIntensity': data['carbonIntensity'],
                    'datetime': data.get('datetime', 'N/A')
                })

        # Sort by carbon intensity
        comparison.sort(key=lambda x: x['carbonIntensity'])

        print(f"\n{'='*75}")
        print(" CARBON INTENSITY RANKING (Cleanest → Dirtiest)")
        print(f"{'='*75}")
        for i, region in enumerate(comparison, 1):
            if i == 1:
                medal = ""
                marker = "← BEST"
            elif i == 2:
                medal = ""
                marker = ""
            elif i == 3:
                medal = ""
                marker = ""
            else:
                medal = f"{i}."
                marker = ""

            display = f"{region['flag']} {region['name']}"
            print(f"{medal} {display:<38} - {region['carbonIntensity']:4d} gCO₂/kWh {marker}")
        print(f"{'='*75}\n")

        return comparison

    def clear_cache(self):
        """Clear the internal cache."""
        self.cache = {}
        print("✓ Cache cleared")

    def get_quick_recommendation(self) -> Optional[Dict]:
        """
        Get a quick deployment recommendation without detailed output.
        Useful for scheduler integration.

        Returns:
            Dict with greenest region info or None if all fetches failed
            {
                'zone': 'FI',
                'name': 'Finland',
                'flag': '',
                'carbonIntensity': 40,
                'savings': 254,
                'averageCarbon': 294
            }
        """
        all_data = self.fetch_all_regions(display_details=False)

        # Filter out failed fetches
        valid_regions = {
            zone: data
            for zone, data in all_data.items()
            if data is not None and 'carbonIntensity' in data
        }

        if not valid_regions:
            return None

        # Find region with minimum carbon intensity
        greenest_zone = min(
            valid_regions.keys(),
            key=lambda z: valid_regions[z]['carbonIntensity']
        )

        greenest_data = valid_regions[greenest_zone]
        avg_carbon = sum(d['carbonIntensity'] for d in valid_regions.values()) / len(valid_regions)
        savings = round(avg_carbon - greenest_data['carbonIntensity'])

        region_info = self.regions[greenest_zone]

        return {
            'zone': greenest_zone,
            'name': region_info['name'],
            'flag': region_info['flag'],
            'carbonIntensity': greenest_data['carbonIntensity'],
            'datetime': greenest_data.get('datetime', 'N/A'),
            'savings': savings,
            'averageCarbon': round(avg_carbon),
            'totalRegions': len(valid_regions)
        }


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Carbon Fetcher module.

    Before running:
    1. Get your API key from https://api-portal.electricitymap.org/
    2. Replace 'YOUR_API_KEY_HERE' below
    """

    print("CASS-Lite v2 - Carbon Fetcher Test")
    print("=" * 60)

    # Initialize fetcher (replace with your actual API key)
    API_KEY = "gwASf8vJiQ92CPIuRzuy"

    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n  WARNING: Please add your ElectricityMap API key first!")
        print("   Get one at: https://api-portal.electricitymap.org/")
        print("   Then update the API_KEY variable in this file.\n")
    else:
        fetcher = CarbonFetcher(api_key=API_KEY, cache_ttl=300)

        # Test 1: Fetch single region
        print("\n--- Test 1: Fetch India ---")
        india_data = fetcher.fetch_carbon_intensity("IN")

        # Test 2: Find greenest region
        print("\n--- Test 2: Find Greenest Region ---")
        greenest = fetcher.get_greenest_region()

        # Test 3: Compare all regions
        print("\n--- Test 3: Compare All Regions ---")
        ranking = fetcher.compare_regions()

        print("\n✓ All tests completed!")
