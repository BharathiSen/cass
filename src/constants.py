# CASS-Lite v2 - Global Metadata Constants
# ============================================

REGION_FLAGS = {
    'IN': '🇮🇳', 
    'FI': '🇫🇮', 
    'DE': '🇩🇪',
    'JP': '🇯🇵', 
    'AU-NSW': '🇦🇺', 
    'BR-CS': '🇧🇷'
}

REGION_NAMES = {
    'IN': 'India (asia-south1)',
    'FI': 'Finland (europe-north1)',
    'DE': 'Germany (europe-west3)',
    'JP': 'Japan (asia-northeast1)',
    'AU-NSW': 'Australia (australia-southeast1)',
    'BR-CS': 'Brazil (southamerica-east1)'
}

# Region coordinates for the Global Heatmap
REGION_MAP_COORDS = {
    'IN': {'lat': 20.5937, 'lon': 78.9629, 'name': 'India'},
    'FI': {'lat': 61.9241, 'lon': 25.7482, 'name': 'Finland'},
    'DE': {'lat': 51.1657, 'lon': 10.4515, 'name': 'Germany'},
    'JP': {'lat': 36.2048, 'lon': 138.2529, 'name': 'Japan'},
    'AU-NSW': {'lat': -31.8406, 'lon': 147.3222, 'name': 'Australia'},
    'BR-CS': {'lat': -15.8267, 'lon': -47.9218, 'name': 'Brazil'}
}

# Carbon simulation ranges (gCO2/kWh)
CARBON_RANGES = {
    'FI': (35, 60),
    'BR-CS': (45, 80),
    'DE': (200, 350),
    'JP': (300, 500),
    'AU-NSW': (400, 700),
    'IN': (600, 850)
}
