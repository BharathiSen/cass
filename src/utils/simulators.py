import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta

try:
    from ..constants import REGION_FLAGS, CARBON_RANGES
except ImportError:
    from src.constants import REGION_FLAGS, CARBON_RANGES

def generate_mock_decisions(count=50):
    """Generate high-fidelity synthetic decision logs for local testing."""
    regions = list(REGION_FLAGS.keys())
    data = []
    base_time = datetime.now()

    for i in range(count):
        # Weighted selection (Finland/Brazil are greenest)
        region = random.choices(regions, weights=[5, 60, 10, 10, 5, 10])[0]
        carbon = random.randint(*CARBON_RANGES[region])
        
        # Simulated savings vs global average (362 gCO2)
        avg_carbon = 362
        savings = max(0, avg_carbon - carbon)
        
        data.append({
            'timestamp': base_time - timedelta(minutes=i * 15),
            'region': region,
            'region_flag': REGION_FLAGS[region],
            'carbon_intensity': carbon,
            'savings_percent': round((savings / avg_carbon) * 100, 1) if avg_carbon > 0 else 0,
            'status': 'success' if random.random() > 0.05 else 'warning',
            'data_source': 'simulation'
        })
    return pd.DataFrame(data)

def generate_mock_history(days=7):
    """Generate synthetic time-series grid telemetry."""
    data = []
    hours = days * 24
    base_time = datetime.now() - timedelta(days=days)

    for region in REGION_FLAGS.keys():
        for hour in range(hours):
            ts = base_time + timedelta(hours=hour)
            base_val = sum(CARBON_RANGES[region]) / 2
            variation = random.uniform(-0.15, 0.15) * base_val
            data.append({
                'timestamp': ts,
                'region': region,
                'carbon_intensity': int(base_val + variation)
            })
    return pd.DataFrame(data)

def generate_mock_energy_mix(days=7):
    """Generate synthetic renewable share trends."""
    timestamps = pd.date_range(end=datetime.now(), periods=days * 24, freq='H')
    data = []
    for ts in timestamps:
        # Sine wave with daily peak (solar)
        solar_factor = np.sin((ts.hour - 6) * np.pi / 12) * 18
        renewable_pct = 60 + solar_factor + np.random.normal(0, 3)
        data.append({
            'timestamp': ts,
            'renewable_pct': np.clip(renewable_pct, 15, 98)
        })
    return pd.DataFrame(data)
