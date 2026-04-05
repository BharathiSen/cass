import pandas as pd
from datetime import datetime, timedelta
from google.cloud import firestore
import streamlit as st

# Import simulator as fallback
try:
    from ..utils.simulators import generate_mock_decisions
except ImportError:
    from src.utils.simulators import generate_mock_decisions

def get_firestore_client():
    """Initialize Firestore with production fallback logic."""
    try:
        # Default Google Application Credentials (GCP Auth)
        return firestore.Client(project="cass-lite")
    except Exception as e:
        return None

def fetch_recent_decisions(limit=50):
    """Fetch orchestration logs from production Firestore or fallback to simulation."""
    db = get_firestore_client()
    if db is None:
        return generate_mock_decisions(limit)

    try:
        docs = (
            db.collection('carbon_logs')
            .order_by('timestamp', direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        decisions = [doc.to_dict() for doc in docs]
        
        if not decisions:
            return generate_mock_decisions(limit)

        df = pd.DataFrame(decisions)
        
        # Data Normalization
        if 'region' not in df.columns and 'selected_region' in df.columns:
            df['region'] = df['selected_region']
            
        df['data_source'] = 'production'
        return df
    except Exception:
        return generate_mock_decisions(limit)

def get_summary_stats(days=7):
    """Perform data-driven trend analysis on recent decisions."""
    df = fetch_recent_decisions(limit=1000)
    if df.empty:
        return {'avg_carbon': 0, 'savings_percent': 0, 'total_decisions': 0}

    # Temporal Filtering
    cutoff_date = datetime.now() - timedelta(days=days)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[df['timestamp'] >= cutoff_date]

    return {
        'avg_carbon': df['carbon_intensity'].mean() if 'carbon_intensity' in df.columns else 0,
        'savings_percent': df['savings_percent'].mean() if 'savings_percent' in df.columns else 0,
        'greenest_region': df['region'].mode()[0] if 'region' in df.columns else 'N/A',
        'total_decisions': len(df),
        'success_rate': (df['status'] == 'success').mean() * 100 if 'status' in df.columns else 100
    }
def persist_decision(decision_data):
    """
    Persists a scheduling decision. In Free Mode (Local), this is a no-op 
    since we rely on real-time grid telemetry for each poll.
    """
    pass
