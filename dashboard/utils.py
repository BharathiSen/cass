"""
CASS-Lite v2 - Dashboard Utilities
===================================
Helper functions for fetching data from Firestore and processing metrics

Author: Bharathi Senthilkumar
Date: November 2025
"""

import pandas as pd
from datetime import datetime, timedelta
from google.cloud import firestore
from google.oauth2 import service_account
import os

# ============================================================================
# FIRESTORE CONNECTION
# ============================================================================

def get_firestore_client():
    """
    Initialize and return Firestore client.

    Returns:
        Firestore client or None if connection fails
    """
    try:
        # Try to use default credentials (works in GCP environment)
        db = firestore.Client(project="cass-lite")
        return db
    except Exception as e:
        print(f"⚠️  Firestore connection failed: {e}")
        print("   Using mock data for dashboard")
        return None

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def fetch_recent_decisions(limit=50):
    """
    Fetch recent scheduling decisions from Firestore.

    Args:
        limit: Maximum number of records to fetch

    Returns:
        pandas DataFrame with decision data
    """
    db = get_firestore_client()

    if db is None:
        # Return mock data if Firestore unavailable
        return generate_mock_decisions(limit)

    try:
        # Query Firestore collection
        docs = (
            db.collection('carbon_logs')
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        # Convert to list of dicts
        decisions = []
        for doc in docs:
            data = doc.to_dict()
            decisions.append(data)

        if not decisions:
            print("📭 No data in Firestore, using mock data")
            return generate_mock_decisions(limit)

        # Convert to DataFrame
        df = pd.DataFrame(decisions)

        # Backward compatibility: normalize region naming
        if 'region' not in df.columns and 'selected_region' in df.columns:
            df['region'] = df['selected_region']
        elif 'region' in df.columns and 'selected_region' in df.columns:
            df['region'] = df['region'].fillna(df['selected_region'])

        # Add display columns
        df['region_flag'] = df['region'].map({
            'IN': '🇮🇳', 'FI': '🇫🇮', 'DE': '🇩🇪',
            'JP': '🇯🇵', 'AU-NSW': '🇦🇺', 'BR-CS': '🇧🇷'
        })
        df['data_source'] = 'real'

        return df

    except Exception as e:
        print(f"⚠️  Error fetching from Firestore: {e}")
        return generate_mock_decisions(limit)

def get_summary_stats(days=7):
    """
    Calculate summary statistics from recent decisions.

    Args:
        days: Number of days to analyze

    Returns:
        Dictionary with summary metrics
    """
    df = fetch_recent_decisions(limit=1000)

    if df.empty:
        return {
            'avg_carbon': 0,
            'savings_percent': 0,
            'greenest_region': 'N/A',
            'greenest_flag': '🌍',
            'total_decisions': 0,
            'success_rate': 0
        }

    # Filter by date range
    if 'timestamp' in df.columns:
        cutoff_date = datetime.now() - timedelta(days=days)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['timestamp'] >= cutoff_date]

    # Calculate metrics
    avg_carbon = df['carbon_intensity'].mean() if 'carbon_intensity' in df.columns else 0

    # Get most common greenest region
    if 'region' in df.columns:
        greenest_region = df['region'].mode()[0]
        region_flags = {
            'IN': '🇮🇳', 'FI': '🇫🇮', 'DE': '🇩🇪',
            'JP': '🇯🇵', 'AU-NSW': '🇦🇺', 'BR-CS': '🇧🇷'
        }
        greenest_flag = region_flags.get(greenest_region, '🌍')
    else:
        greenest_region = 'N/A'
        greenest_flag = '🌍'

    # Calculate average savings
    savings_percent = df['savings_percent'].mean() if 'savings_percent' in df.columns else 0

    # Success rate
    if 'status' in df.columns:
        success_rate = (df['status'] == 'success').mean() * 100
    else:
        success_rate = 100

    latest = df.sort_values('timestamp', ascending=False).iloc[0] if not df.empty else {}
    decision_basis = latest.get('decision_basis', 'instantaneous')
    switch_reason = latest.get('switch_reason', 'n/a')
    last_switched_hours_ago = float(latest.get('last_switched_hours_ago', 0) or 0)
    next_eligible_switch_in_hours = float(latest.get('next_eligible_switch_in_hours', 0) or 0)

    return {
        'avg_carbon': avg_carbon,
        'savings_percent': savings_percent,
        'greenest_region': greenest_region,
        'greenest_flag': greenest_flag,
        'total_decisions': len(df),
        'success_rate': success_rate,
        'decision_basis': decision_basis,
        'switch_reason': switch_reason,
        'last_switched_hours_ago': round(last_switched_hours_ago, 2),
        'next_eligible_switch_in_hours': round(next_eligible_switch_in_hours, 2)
    }

def get_region_history(days=7):
    """
    Get historical carbon intensity data by region.

    Args:
        days: Number of days of history

    Returns:
        pandas DataFrame with time-series data
    """
    df = fetch_recent_decisions(limit=1000)

    if df.empty:
        return generate_mock_history(days)

    # Filter by date range
    if 'timestamp' in df.columns:
        cutoff_date = datetime.now() - timedelta(days=days)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[df['timestamp'] >= cutoff_date]

    # Ensure required columns exist
    required_cols = ['timestamp', 'region', 'carbon_intensity', 'region_flag']
    if not all(col in df.columns for col in required_cols):
        return generate_mock_history(days)

    return df[required_cols].sort_values('timestamp')

def fetch_current_carbon_data():
    """
    Fetch current carbon intensity for all regions.

    Returns:
        Dictionary with current carbon data by region
    """
    df = fetch_recent_decisions(limit=10)

    if df.empty:
        return {}

    # Get most recent entry for each region
    current_data = {}
    for region in df['region'].unique():
        region_df = df[df['region'] == region].sort_values('timestamp', ascending=False)
        if not region_df.empty:
            row = region_df.iloc[0]
            current_data[region] = {
                'carbon_intensity': row.get('carbon_intensity', 0),
                'timestamp': row.get('timestamp', datetime.now()),
                'flag': row.get('region_flag', '🌍')
            }

    return current_data

# ============================================================================
# MOCK DATA GENERATORS (for testing without Firestore)
# ============================================================================

def generate_mock_decisions(count=50):
    """Generate mock decision data for testing."""
    import random

    regions = ['IN', 'FI', 'DE', 'JP', 'AU-NSW', 'BR-CS']
    region_flags = {
        'IN': '🇮🇳', 'FI': '🇫🇮', 'DE': '🇩🇪',
        'JP': '🇯🇵', 'AU-NSW': '🇦🇺', 'BR-CS': '🇧🇷'
    }

    # Carbon intensity ranges (gCO₂/kWh)
    carbon_ranges = {
        'FI': (35, 60),   # Finland - cleanest
        'BR-CS': (45, 80),
        'DE': (200, 350),
        'JP': (300, 500),
        'AU-NSW': (400, 700),
        'IN': (600, 850)  # India - highest
    }

    data = []
    base_time = datetime.now()

    for i in range(count):
        # FI selected most often (it's usually the greenest)
        region = random.choices(
            regions,
            weights=[5, 60, 15, 10, 5, 5]  # FI weighted highest
        )[0]

        carbon_intensity = random.randint(*carbon_ranges[region])
        avg_carbon = 362  # Global average
        savings = max(0, avg_carbon - carbon_intensity)
        savings_percent = (savings / avg_carbon) * 100 if avg_carbon > 0 else 0

        timestamp = base_time - timedelta(hours=i * 0.25)  # Every 15 minutes

        data.append({
            'timestamp': timestamp,
            'region': region,
            'region_flag': region_flags[region],
            'carbon_intensity': carbon_intensity,
            'savings_gco2': savings,
            'savings_percent': round(savings_percent, 1),
            'status': 'success' if random.random() > 0.05 else 'warning',
            'decision_time_ms': random.randint(3000, 8000),
            'data_source': 'mock'
        })

    return pd.DataFrame(data)

def generate_mock_history(days=7):
    """Generate mock historical time-series data."""
    import random

    regions = ['IN', 'FI', 'DE', 'JP', 'AU-NSW', 'BR-CS']
    region_flags = {
        'IN': '🇮🇳', 'FI': '🇫🇮', 'DE': '🇩🇪',
        'JP': '🇯🇵', 'AU-NSW': '🇦🇺', 'BR-CS': '🇧🇷'
    }

    carbon_ranges = {
        'FI': (35, 60),
        'BR-CS': (45, 80),
        'DE': (200, 350),
        'JP': (300, 500),
        'AU-NSW': (400, 700),
        'IN': (600, 850)
    }

    data = []
    hours = days * 24
    base_time = datetime.now() - timedelta(days=days)

    for region in regions:
        for hour in range(hours):
            timestamp = base_time + timedelta(hours=hour)
            base_carbon = sum(carbon_ranges[region]) / 2
            variation = random.uniform(-0.2, 0.2) * base_carbon
            carbon_intensity = int(base_carbon + variation)

            data.append({
                'timestamp': timestamp,
                'region': region,
                'region_flag': region_flags[region],
                'carbon_intensity': carbon_intensity
            })

    return pd.DataFrame(data)

# ============================================================================
# DATA PROCESSING HELPERS
# ============================================================================

def calculate_carbon_savings(selected_carbon, all_carbons):
    """
    Calculate carbon savings compared to alternatives.

    Args:
        selected_carbon: Carbon intensity of selected region
        all_carbons: List of carbon intensities from all regions

    Returns:
        Tuple of (savings_gco2, savings_percent)
    """
    if not all_carbons:
        return 0, 0

    avg_carbon = sum(all_carbons) / len(all_carbons)
    savings_gco2 = max(0, avg_carbon - selected_carbon)
    savings_percent = (savings_gco2 / avg_carbon * 100) if avg_carbon > 0 else 0

    return round(savings_gco2, 1), round(savings_percent, 1)

def format_timestamp(timestamp):
    """Format timestamp for display."""
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def get_region_color(carbon_intensity):
    """
    Get color code based on carbon intensity.

    Args:
        carbon_intensity: Carbon intensity value

    Returns:
        Color code (green, yellow, red)
    """
    if carbon_intensity < 100:
        return '#00ff88'  # Green - very clean
    elif carbon_intensity < 300:
        return '#ffc107'  # Yellow - moderate
    else:
        return '#ff0066'  # Red - high carbon

def get_energy_mix_data(days=7):
    """
    Get energy mix data (renewable vs fossil) over time.
    Uses carbon intensity as proxy for energy mix when real data unavailable.

    Args:
        days: Number of days of historical data

    Returns:
        DataFrame with timestamp and renewable_pct columns
    """
    import numpy as np

    try:
        # Fetch recent decisions
        recent_logs = fetch_recent_decisions(limit=1000)

        if recent_logs.empty or 'carbon_intensity' not in recent_logs.columns:
            # Generate synthetic data
            return generate_mock_energy_mix(days)

        # Filter by date range
        if 'timestamp' in recent_logs.columns:
            cutoff = datetime.now() - timedelta(days=days)
            recent_logs['timestamp'] = pd.to_datetime(recent_logs['timestamp'])
            recent_logs = recent_logs[recent_logs['timestamp'] >= cutoff]

        # Use carbon intensity as proxy for renewable percentage
        # Lower carbon = higher renewable percentage
        # Typical ranges: 0-100 gCO2/kWh = 90-100% renewable
        #                 100-300 gCO2/kWh = 50-90% renewable
        #                 300+ gCO2/kWh = 0-50% renewable

        def carbon_to_renewable_pct(carbon):
            """Convert carbon intensity to estimated renewable percentage"""
            if carbon < 100:
                return 90 + (100 - carbon) / 10
            elif carbon < 300:
                return 50 + (300 - carbon) / 5
            else:
                return max(0, 50 - (carbon - 300) / 10)

        recent_logs['renewable_pct'] = recent_logs['carbon_intensity'].apply(carbon_to_renewable_pct)
        recent_logs['renewable_pct'] = recent_logs['renewable_pct'].clip(0, 100)

        # Group by hour for smoother visualization
        recent_logs['hour'] = recent_logs['timestamp'].dt.floor('H')
        energy_mix = recent_logs.groupby('hour').agg({
            'renewable_pct': 'mean'
        }).reset_index()
        energy_mix.rename(columns={'hour': 'timestamp'}, inplace=True)

        return energy_mix

    except Exception as e:
        print(f"Error generating energy mix data: {e}")
        return generate_mock_energy_mix(days)

def generate_mock_energy_mix(days=7):
    """Generate mock energy mix data for visualization"""
    import numpy as np

    timestamps = pd.date_range(
        end=datetime.now(),
        periods=days * 24,  # Hourly data
        freq='H'
    )

    # Simulate renewable percentage with daily and hourly patterns
    base_renewable = 65  # Base renewable percentage

    data = []
    for i, ts in enumerate(timestamps):
        # Daily variation (solar peaks during day)
        hour_factor = np.sin((ts.hour - 6) * np.pi / 12) * 15  # Peak at noon

        # Weekly variation
        day_factor = np.sin(i * np.pi / (24 * 7)) * 10

        # Random noise
        noise = np.random.normal(0, 5)

        renewable_pct = base_renewable + hour_factor + day_factor + noise
        renewable_pct = np.clip(renewable_pct, 20, 95)

        data.append({
            'timestamp': ts,
            'renewable_pct': renewable_pct
        })

    return pd.DataFrame(data)

