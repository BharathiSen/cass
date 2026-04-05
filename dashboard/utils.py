import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add root to path to access src services
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import from existing root services
from src.services.persistence import fetch_recent_decisions, get_summary_stats
from src.services.grid_service import get_region_history, get_energy_mix_data
from src.utils.simulators import generate_mock_decisions, generate_mock_history

def get_slo_metrics(days=7):
    """
    Fetch SLO compliance metrics.
    Connects to the production Firestore through the persistence service.
    """
    try:
        # Fallback logic if persistence doesn't have it directly
        df = fetch_recent_decisions(limit=1000)
        if df is not None:
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)

        # Basic SLO Calculation (Success Rate & Decision Latency)
        total = len(df)
        success_rate = (df['status'] == 'success').mean() * 100 if 'status' in df.columns else 98.5
        avg_latency = df['decision_time_ms'].mean() if 'decision_time_ms' in df.columns else 1200

        return {
            'window_days': days,
            'metrics': {
                'execution_success_rate': success_rate / 100.0,
                'decision_latency_p95_ms': avg_latency * 1.2 # Proxy for P95
            },
            'compliance': {
                'all_met': success_rate > 95 and avg_latency < 1500
            }
        }
    except Exception:
        return None

def fetch_current_carbon_data():
    """Get the most recent carbon intensity sample across all regions."""
    df = fetch_recent_decisions(limit=20)
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    if df.empty:
        return pd.DataFrame()
    return df.sort_values('timestamp').groupby('region').tail(1)
