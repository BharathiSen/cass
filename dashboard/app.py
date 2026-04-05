import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import sys
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

# Add root directory to sys.path to ensure modules in src/ are discoverable
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import local modules from re-organized src/ structure
from dashboard.utils import (
    fetch_recent_decisions,
    get_summary_stats,
    get_slo_metrics,
    fetch_current_carbon_data,
    get_region_history,
    get_energy_mix_data,
    generate_mock_decisions,
    generate_mock_history
)

from src.styles.design_system import apply_custom_css, apply_high_contrast_css
from src.components.layout import render_hero, render_footer
from src.components.metrics import render_metrics, render_slo_cards, render_impact_metrics_strip
from src.components.charts import (
    render_carbon_intensity_chart, 
    render_geographic_map, 
    render_savings_gauge,
    render_energy_mix_chart,
    render_region_frequency_chart
)
from src.components.audit import (
    render_logs_table, 
    render_multi_objective_optimizer, 
    render_export_section,
    render_why_this_is_hard,
    render_results_section,
    render_engineering_decisions
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="CASS | Carbon-Aware Scheduler",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STATE MANAGEMENT & STYLING
# ============================================================================

if 'high_contrast' not in st.session_state:
    st.session_state.high_contrast = False

apply_custom_css()
if st.session_state.high_contrast:
    apply_high_contrast_css()

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    render_hero()

    # Sidebar controls
    with st.sidebar:
        st.markdown("## Dashboard Controls")
        st.markdown("---")

        st.markdown("#### Accessibility")
        high_contrast = st.checkbox(
            "High Contrast Mode",
            value=st.session_state.high_contrast,
            help="Toggle high contrast mode for better visibility"
        )
        if high_contrast != st.session_state.high_contrast:
            st.session_state.high_contrast = high_contrast
            st.rerun()

        st.markdown("---")
        st.markdown("#### Data Range")
        days_filter = st.selectbox("Show last", [1, 3, 7, 14, 30], index=2)

        st.markdown("---")
        if st.button("Refresh Data", width='stretch'):
            st.rerun()

        st.markdown("---")
        st.markdown("#### Project Info")
        st.markdown("""
        **Project:** CASS-Lite v2
        **Status:** Local-First (Free Mode)
        **Region:** Multi-region Orchestration
        """)

    # Data Loading Logic
    with st.spinner("Loading grid intelligence..."):
        stats = get_summary_stats(days=days_filter)
        recent_logs = fetch_recent_decisions(limit=100)
        slo_snapshot = get_slo_metrics(days=days_filter)
        region_history = get_region_history(days=days_filter)
        time.sleep(0.1)

    # Layout Rendering
    if stats:
        render_metrics(stats)
        
    if slo_snapshot:
        render_slo_cards(slo_snapshot)

    if stats is not None and not recent_logs.empty:
        # render_impact_metrics_strip(stats, recent_logs) # Optional strip
        # render_why_this_is_hard()
        # render_results_section(stats, recent_logs)
        render_engineering_decisions()

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        if not region_history.empty:
            render_carbon_intensity_chart(region_history)
    with col2:
        if stats:
            render_savings_gauge(stats.get('savings_percent', 0))

    if not recent_logs.empty:
        render_geographic_map(recent_logs)

    col3, col4 = st.columns(2)
    with col3:
        if not recent_logs.empty:
            render_region_frequency_chart(recent_logs)
    with col4:
        render_energy_mix_chart(days=days_filter)

    render_multi_objective_optimizer(recent_logs=recent_logs)
    render_logs_table(recent_logs)
    
    if not recent_logs.empty:
        render_export_section(recent_logs)

    render_footer()

if __name__ == "__main__":
    main()
