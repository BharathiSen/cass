import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Import Persistence and Simulators
try:
    from .persistence import fetch_recent_decisions
    from ..utils.simulators import generate_mock_energy_mix
except ImportError:
    from src.services.persistence import fetch_recent_decisions
    from src.utils.simulators import generate_mock_energy_mix

def get_energy_mix_data(days=7):
    """
    Get renewable vs fossil share trajectory.
    Uses carbon intensity as proxy when real-time mix telemetry is unavailable.
    """
    try:
        logs = fetch_recent_decisions(limit=1000)
        if logs.empty or 'carbon_intensity' not in logs.columns:
            return generate_mock_energy_mix(days)

        # Filtering
        cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
        logs['timestamp'] = pd.to_datetime(logs['timestamp'], format='mixed', errors='coerce', utc=True)
        logs = logs.dropna(subset=['timestamp'])
        if logs.empty:
            return generate_mock_energy_mix(days)
        logs = logs[logs[ 'timestamp'] >= cutoff]

        # PROXY LOGIC: Convert gCO2/kWh to Renewables %
        # (Lower intensity = Higher renewable penetration)
        def carbon_to_renewable_pct(carbon):
            if carbon < 100: return 90 + (100 - carbon) / 10
            elif carbon < 300: return 50 + (300 - carbon) / 5
            return max(10, 50 - (carbon - 300) / 10)

        logs['renewable_pct'] = logs['carbon_intensity'].apply(carbon_to_renewable_pct).clip(15, 100)

        # Smoothed grouping
        logs['hour'] = logs['timestamp'].dt.floor('H')
        return logs.groupby('hour').agg({'renewable_pct': 'mean'}).reset_index().rename(columns={'hour': 'timestamp'})

    except Exception:
        return generate_mock_energy_mix(days)

def get_region_history(days=7):
    """Fetch global intensity trajectory (historical time-series)."""
    # This currently uses recent decisions as a proxy for history
    # In a full production env, this would pull from a dedicated timeseries collection
    return fetch_recent_decisions(limit=2000)
