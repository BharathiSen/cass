"""
CASS-Lite v2 - Carbon-Aware Serverless Scheduler Dashboard
===========================================================
Phase 9: Intelligent Visualization & Professional UX
Futuristic Streamlit Dashboard with Real-time Carbon Intelligence

Author: Bharathi Senthilkumar
Date: November 2025
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import json
from utils import (
    fetch_recent_decisions,
    get_summary_stats,
    fetch_current_carbon_data,
    get_region_history,
    get_energy_mix_data,
    generate_mock_decisions,
    generate_mock_history
)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="CASS-Lite v2 - Carbon-Aware Serverless Scheduler Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for high contrast mode
if 'high_contrast' not in st.session_state:
    st.session_state.high_contrast = False
if 'data_loading_failed' not in st.session_state:
    st.session_state.data_loading_failed = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_skeleton_loader():
    """Render skeleton loader for data loading state"""
    st.markdown("""
    <div class="skeleton" style="height: 150px; margin: 10px 0;"></div>
    <div class="skeleton" style="height: 150px; margin: 10px 0;"></div>
    <div class="skeleton" style="height: 300px; margin: 10px 0;"></div>
    """, unsafe_allow_html=True)

def apply_high_contrast_css():
    """Apply high contrast CSS overrides"""
    if st.session_state.high_contrast:
        st.markdown("""
        <style>
            .stApp {
                background: #000000 !important;
            }
            .stMarkdown, .stMarkdown p, .stMarkdown span, .metric-label, .metric-value {
                color: #FFFFFF !important;
            }
            .hero-title {
                background: linear-gradient(90deg, #FFFFFF 0%, #FFFF00 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .metric-card, .chart-container {
                background: #1a1a1a !important;
                border: 2px solid #FFFFFF !important;
            }
            .chart-title {
                color: #FFFF00 !important;
            }
            .insight-card {
                background: #1a1a1a !important;
                border-left: 4px solid #FFFF00 !important;
                color: #FFFFFF !important;
                min-height: 160px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .insight-card *,
            .insight-card h1,
            .insight-card h2,
            .insight-card h3,
            .insight-card h4,
            .insight-card h5,
            .insight-card h6,
            .insight-card p,
            .insight-card span,
            .insight-card div,
            .insight-card strong,
            .insight-card em,
            .insight-card a {
                font-family: 'Orbitron', monospace !important;
            }
            .insight-title {
                color: #FFFF00 !important;
                font-family: 'Orbitron', monospace !important;
                font-weight: 600 !important;
            }
            .insight-text {
                color: #FFFFFF !important;
                font-family: 'Orbitron', monospace !important;
            }
            .insight-metric {
                background: #FFFF00 !important;
                color: #000000 !important;
                font-family: 'Orbitron', monospace !important;
                font-weight: 700 !important;
            }
        </style>
        """, unsafe_allow_html=True)

# ============================================================================
# CUSTOM CSS - FUTURISTIC NEON THEME
# ============================================================================

st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;900&display=swap');

    /* Global Typography - Orbitron Futuristic Sci-Fi Style */
    * {
        font-family: 'Orbitron', monospace !important;
        letter-spacing: 0.05em !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Orbitron', monospace !important;
    }

    /* Typography Hierarchy - All Orbitron */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        line-height: 1.4 !important;
    }

    h1 {
        font-size: 2.5rem !important;
        font-weight: 900 !important;
    }

    h2 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    h3 {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
    }

    h4 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    h5, h6 {
        font-size: 1rem !important;
        font-weight: 500 !important;
    }

    /* Body Text */
    p, span, div, label, input, textarea, select {
        font-family: 'Orbitron', monospace !important;
        font-weight: 400 !important;
        letter-spacing: 0.05em !important;
        line-height: 1.6 !important;
    }

    /* Streamlit Components */
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div {
        font-family: 'Orbitron', monospace !important;
        letter-spacing: 0.05em !important;
    }

    .stButton button, .stDownloadButton button {
        font-family: 'Orbitron', monospace !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
    }

    .stSelectbox, .stMultiSelect, .stTextInput, .stTextArea {
        font-family: 'Orbitron', monospace !important;
        font-weight: 400 !important;
    }

    .stMetric, .stMetric label, .stMetric div {
        font-family: 'Orbitron', monospace !important;
        letter-spacing: 0.05em !important;
    }

    .stMetric label {
        font-weight: 500 !important;
    }

    .stMetric [data-testid="stMetricValue"] {
        font-weight: 700 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"], [data-testid="stSidebar"] * {
        font-family: 'Orbitron', monospace !important;
        letter-spacing: 0.05em !important;
    }

    /* Loading Skeleton */
    .skeleton {
        background: linear-gradient(90deg, rgba(255,255,255,0.1) 25%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 75%);
        background-size: 200% 100%;
        animation: loading 1.5s ease-in-out infinite;
        border-radius: 10px;
    }

    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    /* Ensure Streamlit columns are uniform */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
    }

    [data-testid="column"] > div {
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    /* Hero Header */
    .hero-header {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 255, 255, 0.2);
        animation: glow-pulse 3s ease-in-out infinite;
    }

    @keyframes glow-pulse {
        0%, 100% { box-shadow: 0 8px 32px rgba(0, 255, 255, 0.2); }
        50% { box-shadow: 0 8px 48px rgba(0, 255, 255, 0.4); }
    }

    .hero-title {
        font-family: 'Orbitron', monospace !important;
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: 0.05em;
        background: linear-gradient(90deg, #00ffff 0%, #7f00ff 50%, #00ff88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .hero-subtitle {
        font-family: 'Orbitron', monospace !important;
        font-size: 1.3rem;
        color: #00ffaa;
        text-align: center;
        font-weight: 500;
        letter-spacing: 0.1em;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Live Carbon Ticker */
    .carbon-ticker {
        background: linear-gradient(90deg, rgba(0, 255, 255, 0.2) 0%, rgba(127, 0, 255, 0.2) 100%);
        border: 1px solid rgba(0, 255, 255, 0.4);
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
        font-size: 1.2rem;
        color: #00ffff;
        font-family: 'Orbitron', monospace !important;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-top: 1rem;
        animation: ticker-glow 2s ease-in-out infinite;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    @keyframes ticker-glow {
        0%, 100% { border-color: rgba(0, 255, 255, 0.4); }
        50% { border-color: rgba(0, 255, 255, 0.8); }
    }

    .hero-ownership {
        margin-top: 0.9rem;
        text-align: center;
        color: #d7f7ff;
        font-size: 0.95rem;
        line-height: 1.55;
        background: rgba(0, 18, 32, 0.45);
        border: 1px solid rgba(0, 255, 170, 0.35);
        border-radius: 10px;
        padding: 0.7rem 0.8rem;
    }

    .hero-ownership strong {
        color: #00ffaa;
    }

    .impact-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.35rem 0 1.2rem 0;
    }

    .impact-card {
        border: 1px solid rgba(0, 255, 255, 0.25);
        border-radius: 12px;
        padding: 0.9rem;
        background: linear-gradient(145deg, rgba(12, 22, 40, 0.72) 0%, rgba(7, 48, 76, 0.35) 100%);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.22);
    }

    .impact-label {
        font-size: 0.78rem;
        color: #8fd6ff;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    .impact-value {
        font-size: 1.35rem;
        color: #ffffff;
        font-weight: 800;
        line-height: 1.2;
    }

    .impact-subtext {
        margin-top: 0.2rem;
        font-size: 0.78rem;
        color: #8ba7c5;
    }

    .hard-section {
        margin: 0.3rem 0 1.1rem 0;
        padding: 0.9rem;
        border: 1px solid rgba(0, 212, 255, 0.22);
        border-radius: 14px;
        background: linear-gradient(145deg, rgba(10, 22, 44, 0.72) 0%, rgba(5, 36, 62, 0.3) 100%);
    }

    .hard-title {
        font-size: 0.9rem;
        color: #d6f7ff;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 0.7rem;
        letter-spacing: 0.06em;
    }

    .hard-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.7rem;
    }

    .hard-card {
        border: 1px solid rgba(149, 190, 255, 0.22);
        border-radius: 12px;
        padding: 0.75rem;
        background: rgba(255, 255, 255, 0.03);
        min-height: 98px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .hard-card-title {
        color: #dff6ff;
        font-size: 0.84rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .hard-card-text {
        color: #a8c3e3;
        font-size: 0.74rem;
        line-height: 1.35;
    }

    .repo-source-card {
        margin-top: 0.7rem;
        padding: 0.8rem 0.95rem;
        border-radius: 12px;
        border: 1px solid rgba(0, 255, 170, 0.28);
        background: linear-gradient(145deg, rgba(10, 22, 44, 0.78) 0%, rgba(5, 36, 62, 0.38) 100%);
        text-align: center;
    }

    .repo-source-title {
        color: #c8fbff;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .repo-source-link {
        display: inline-block;
        font-size: 0.84rem;
        color: #00ffaa;
        text-decoration: none;
        border-bottom: 1px solid rgba(0, 255, 170, 0.35);
        padding-bottom: 2px;
    }

    .repo-source-link:hover {
        color: #9bffdb;
        border-bottom-color: rgba(155, 255, 219, 0.7);
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(10, 14, 39, 0.8) 0%, rgba(26, 26, 46, 0.8) 100%);
        border: 2px solid rgba(0, 255, 255, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 255, 255, 0.15);
        transition: all 0.3s ease;
        height: 100%;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .metric-card:hover {
        border-color: rgba(0, 255, 255, 0.6);
        box-shadow: 0 8px 40px rgba(0, 255, 255, 0.3);
        transform: translateY(-5px);
    }

    .metric-label {
        font-family: 'Orbitron', monospace !important;
        font-size: 0.9rem;
        color: #00ffaa;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
        margin-bottom: 0.5rem;
        min-height: 2.6rem;
        text-shadow: 0 0 10px rgba(0, 255, 170, 0.5);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .metric-value {
        font-family: 'Orbitron', monospace !important;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        background: linear-gradient(90deg, #00ffff 0%, #00ff88 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        line-height: 1.2;
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }

    .metric-delta {
        font-family: 'Orbitron', monospace !important;
        font-size: 0.85rem;
        color: #9333ea;
        font-weight: 500;
        letter-spacing: 0.05em;
        min-height: 24px;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Chart Container */
    .chart-container {
        background: linear-gradient(135deg, rgba(10, 14, 39, 0.6) 0%, rgba(26, 26, 46, 0.6) 100%);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        margin-bottom: 1.5rem;
    }

    .chart-title {
        font-family: 'Orbitron', monospace !important;
        font-size: 1.3rem;
        color: #ffffff;
        margin-bottom: 1rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        line-height: 1.4;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Table Styles */
    .dataframe {
        background: rgba(10, 14, 39, 0.8) !important;
        border: 1px solid rgba(0, 255, 255, 0.2) !important;
        border-radius: 10px;
        font-family: 'Orbitron', monospace !important;
    }

    .dataframe th {
        background: linear-gradient(90deg, rgba(0, 255, 255, 0.2) 0%, rgba(147, 51, 234, 0.2) 100%) !important;
        color: #00ffff !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .dataframe td {
        color: #a0aec0 !important;
        border-color: rgba(0, 255, 255, 0.1) !important;
        font-family: 'Orbitron', monospace !important;
        font-weight: 400;
        letter-spacing: 0.05em;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(0, 255, 255, 0.2);
        color: #00ffaa;
        font-family: 'Orbitron', monospace !important;
        font-size: 0.9rem;
        font-weight: 500;
        letter-spacing: 0.05em;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .footer-icon {
        color: #ff0066;
        animation: heartbeat 1.5s ease-in-out infinite;
    }

    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0a0e27 0%, #1a1a2e 100%);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00ffff 0%, #7f00ff 100%);
        color: #0a0e27;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700;
        letter-spacing: 0.05em;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
        transform: scale(1.05);
    }

    /* Phase 9 Enhancements */

    /* Animated Background Gradient */
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #0a0e27, #1a1a2e, #16213e, #1a0a3e);
        background-size: 400% 400%;
        animation: gradient-shift 15s ease infinite;
    }

    /* Fade-in animations for cards */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .metric-card {
        animation: fadeInUp 0.6s ease-out;
        animation-fill-mode: both;
    }

    .metric-card:nth-child(1) { animation-delay: 0.1s; }
    .metric-card:nth-child(2) { animation-delay: 0.2s; }
    .metric-card:nth-child(3) { animation-delay: 0.3s; }
    .metric-card:nth-child(4) { animation-delay: 0.4s; }

    /* Insight Cards */
    .insight-card {
        background: linear-gradient(135deg, rgba(147, 51, 234, 0.2) 0%, rgba(0, 255, 170, 0.2) 100%);
        border-left: 4px solid #00ffaa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.5s ease-out;
        width: 100%;
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        font-family: 'Orbitron', monospace !important;
    }

    /* High specificity override for ALL elements inside insight cards */
    .insight-card *,
    .insight-card h1,
    .insight-card h2,
    .insight-card h3,
    .insight-card h4,
    .insight-card h5,
    .insight-card h6,
    .insight-card p,
    .insight-card span,
    .insight-card div,
    .insight-card strong,
    .insight-card em,
    .insight-card a {
        font-family: 'Orbitron', monospace !important;
    }

    .insight-title {
        font-family: 'Orbitron', monospace !important;
        font-size: 1rem;
        color: #00ffaa;
        font-weight: 600 !important;
        margin-bottom: 0.75rem;
        letter-spacing: 0.05em;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .insight-text {
        font-family: 'Orbitron', monospace !important;
        color: #a0aec0;
        font-size: 0.95rem;
        line-height: 1.6;
        font-weight: 400 !important;
        letter-spacing: 0.05em;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .insight-metric {
        display: inline-block;
        background: rgba(0, 255, 170, 0.2);
        color: #00ffff;
        padding: 0.2rem 0.6rem;
        border-radius: 5px;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em;
        margin: 0 0.2rem;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Theme Toggle */
    .theme-toggle {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: rgba(0, 255, 255, 0.2);
        border: 1px solid rgba(0, 255, 255, 0.4);
        border-radius: 50px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .theme-toggle:hover {
        background: rgba(0, 255, 255, 0.4);
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.6);
    }

    /* Export Button Styling */
    .stDownloadButton>button {
        background: linear-gradient(90deg, #00ff88 0%, #00ffff 100%);
        color: #0a0e27;
        font-family: 'Orbitron', monospace !important;
        font-weight: 700;
        letter-spacing: 0.05em;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-size: 0.95rem;
        height: 56px;
        min-height: 56px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1;
        transition: all 0.3s ease;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .stDownloadButton>button:hover {
        box-shadow: 0 0 20px rgba(0, 255, 170, 0.6);
        transform: scale(1.05);
    }

    /* Geographic Map Container */
    .geo-map-container {
        background: linear-gradient(135deg, rgba(10, 14, 39, 0.7) 0%, rgba(26, 26, 46, 0.7) 100%);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Loading Spinner Custom */
    .stSpinner > div {
        border-color: #00ffff transparent transparent transparent !important;
    }

    /* Refresh Indicator */
    .refresh-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0, 255, 170, 0.9);
        color: #0a0e27;
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.85rem;
        z-index: 1000;
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.05); }
    }

    /* Section Divider */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #00ffff 50%, transparent 100%);
        margin: 2rem 0;
        opacity: 0.3;
    }

    /* Multi-Objective Optimizer Custom Styles */
    .equal-card {
        min-height: 420px;
        height: auto;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: stretch;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
        padding: 25px;
        transition: all 0.3s ease;
        overflow: visible;
    }

    .equal-card:hover {
        border-color: rgba(0, 212, 255, 0.3);
        box-shadow: 0 12px 35px rgba(0, 212, 255, 0.2);
        transform: translateY(-3px);
    }

    /* Section Title Glassmorphism */
    .section-title {
        padding: 12px 20px;
        border-radius: 12px;
        backdrop-filter: blur(8px);
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        font-family: 'Orbitron', monospace !important;
        font-size: 1.3rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        line-height: 1.4;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        animation: fadeDown 0.6s ease;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .section-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        width: 0;
        height: 2px;
        background: linear-gradient(90deg, #8A2BE2, #1E90FF, #00E1FF);
        transition: all 0.4s ease;
        transform: translateX(-50%);
    }

    .section-title:hover::after {
        width: 100%;
    }

    @keyframes fadeDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Entrance Animations */
    @keyframes fadeLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes fadeRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.95);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    .anim-left {
        animation: fadeLeft 0.8s ease;
    }

    .anim-center {
        animation: fadeInScale 1.0s ease;
    }

    .anim-right {
        animation: fadeRight 0.8s ease;
    }

    /* Neon Gradient Divider */
    .neon-divider {
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #8A2BE2, #1E90FF, #00E1FF);
        margin-top: 35px;
        margin-bottom: 20px;
        border-radius: 2px;
        box-shadow: 0 0 10px rgba(0, 225, 255, 0.5);
    }

    /* Pareto Container with Neon Border */
    .pareto-container {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(0, 225, 255, 0.3);
        border-radius: 20px;
        padding: 25px;
        margin-top: 20px;
        box-shadow: 0 0 20px rgba(0, 225, 255, 0.15);
    }

    .pareto-header {
        background: linear-gradient(90deg, #8A2BE2, #1E90FF, #00E1FF);
        padding: 15px 20px;
        border-radius: 12px 12px 0 0;
        margin: -25px -25px 20px -25px;
        text-align: center;
        color: white;
        font-family: 'Orbitron', monospace;
        font-size: 1.2rem;
        font-weight: 600;
    }

    /* Insights Panel */
    .insights-panel {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 25px;
        margin-top: 20px;
    }

    .insight-summary {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(138, 43, 226, 0.1));
        border-left: 4px solid #00d4ff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }

    .insight-bullets {
        list-style: none;
        padding-left: 0;
        font-family: 'Orbitron', monospace !important;
    }

    .insight-bullets li {
        padding: 8px 0;
        padding-left: 25px;
        position: relative;
        color: #b0b0b0;
        font-family: 'Orbitron', monospace !important;
        font-weight: 400;
        letter-spacing: 0.05em;
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .insight-bullets li::before {
        content: 'â–¶';
        position: absolute;
        left: 0;
        color: #00d4ff;
        font-size: 0.8rem;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .impact-strip {
            grid-template-columns: 1fr 1fr;
        }

        .hard-grid {
            grid-template-columns: 1fr;
        }

        .equal-card {
            min-height: auto;
            margin-bottom: 15px;
        }

        .section-title {
            font-size: 1.1rem;
            padding: 10px 15px;
        }
    }

    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
        transform: scale(1.05);
    }

    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-family: 'Orbitron', monospace !important;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .status-success {
        background: rgba(0, 255, 136, 0.2);
        border: 1px solid #00ff88;
        color: #00ff88;
    }

    .status-warning {
        background: rgba(255, 193, 7, 0.2);
        border: 1px solid #ffc107;
        color: #ffc107;
    }

    /* Tab Labels - Match AI Insights & Predictions Typography */
    [data-baseweb="tab"] button,
    [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab-list"] button,
    .stTabs [data-baseweb="tab-list"] button p,
    .stTabs [data-baseweb="tab-list"] button div {
        font-family: 'Orbitron', monospace !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        line-height: 1.4 !important;
        color: #ffffff !important;
        text-transform: none !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
    }

    /* Tab active state with neon glow */
    [data-baseweb="tab"][aria-selected="true"] button,
    [data-baseweb="tab"][aria-selected="true"] button p {
        color: #00ffff !important;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.6),
                     0 0 20px rgba(0, 255, 255, 0.4),
                     0 0 30px rgba(0, 255, 255, 0.2) !important;
    }

    /* Tab hover state */
    [data-baseweb="tab"] button:hover,
    [data-baseweb="tab"] button:hover p {
        color: #00d4ff !important;
        text-shadow: 0 0 8px rgba(0, 212, 255, 0.5) !important;
    }

    /* Tab underline/border */
    [data-baseweb="tab-highlight] {
        background-color: #00ffff !important;
        box-shadow: 0 0 10px rgba(0, 255, 255, 0.8) !important;
    }

    /* Tab border styling */
    [data-baseweb="tab-border"] {
        background-color: rgba(0, 255, 255, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HERO SECTION
# ============================================================================

def render_hero():
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">CASS</h1>
        <p class="hero-subtitle">A carbon-aware cloud workload scheduler that reduces emissions while balancing latency and cost.</p>
        <div class="carbon-ticker">
             Real-time region decisions with production-safe deployment stability.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# METRIC CARDS
# ============================================================================

def render_metrics(stats):
    """Render metric cards with skeleton loaders for empty data"""
    col1, col2, col3, col4 = st.columns(4)

    # Check if stats is empty or None
    if not stats or stats.get('total_decisions', 0) == 0:
        # Render skeleton loaders
        for col in [col1, col2, col3, col4]:
            with col:
                st.markdown("""
                <div class="skeleton" style="height: 150px;"></div>
                """, unsafe_allow_html=True)
        return

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Carbon Intensity</div>
            <div class="metric-value">{stats.get('avg_carbon', 0):.1f}</div>
            <div class="metric-delta">gCOâ‚‚/kWh</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Carbon Savings</div>
            <div class="metric-value">{stats.get('savings_percent', 0):.1f}%</div>
            <div class="metric-delta">vs Average</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Greenest Region</div>
            <div class="metric-value">{stats.get('greenest_region', 'N/A')}</div>
            <div class="metric-delta">{stats.get('greenest_flag')}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Decisions</div>
            <div class="metric-value">{stats.get('total_decisions', 0)}</div>
            <div class="metric-delta">Last 7 days</div>
        </div>
        """, unsafe_allow_html=True)


def render_impact_metrics_strip(stats, recent_logs):
    """Render recruiter-facing impact metrics using live dashboard data."""
    if not stats:
        return

    carbon_reduction = float(stats.get('savings_percent', 0) or 0)
    decision_accuracy = float(stats.get('success_rate', 0) or 0)

    avg_response_ms = None
    for col in ["execution_time_ms", "response_time_ms", "latency_ms"]:
        if col in recent_logs.columns:
            numeric = pd.to_numeric(recent_logs[col], errors="coerce").dropna()
            if not numeric.empty:
                avg_response_ms = float(numeric.mean())
                break

    if avg_response_ms is None and "latency" in recent_logs.columns:
        numeric = pd.to_numeric(recent_logs["latency"], errors="coerce").dropna()
        if not numeric.empty:
            avg_response_ms = float(numeric.mean())

    uptime = decision_accuracy
    if "status" in recent_logs.columns and not recent_logs.empty:
        normalized_status = recent_logs["status"].astype(str).str.lower().str.strip()
        uptime = float((normalized_status != "failed").mean() * 100)

    response_value = f"{avg_response_ms:.0f} ms" if avg_response_ms is not None else "N/A"

    st.markdown(f"""
    <div class="impact-strip">
        <div class="impact-card">
            <div class="impact-label">Carbon Reduction</div>
            <div class="impact-value">{carbon_reduction:.1f}%</div>
            <div class="impact-subtext">vs baseline average</div>
        </div>
        <div class="impact-card">
            <div class="impact-label">Decision Accuracy</div>
            <div class="impact-value">{decision_accuracy:.1f}%</div>
            <div class="impact-subtext">successful scheduler outcomes</div>
        </div>
        <div class="impact-card">
            <div class="impact-label">Avg Response Time</div>
            <div class="impact-value">{response_value}</div>
            <div class="impact-subtext">mean execution latency</div>
        </div>
        <div class="impact-card">
            <div class="impact-label">Platform Uptime</div>
            <div class="impact-value">{uptime:.1f}%</div>
            <div class="impact-subtext">non-failure service health</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_why_this_is_hard():
    """Render concise explanation of core scheduling complexity."""
    st.markdown("""
    <div class="hard-section">
        <div class="hard-title">Why This Is Hard</div>
        <div class="hard-grid">
            <div class="hard-card">
                <div class="hard-card-title">Real-time Carbon Volatility</div>
                <div class="hard-card-text">Regional grid intensity changes quickly, so static routing can become suboptimal within minutes.</div>
            </div>
            <div class="hard-card">
                <div class="hard-card-title">Anti-Thrashing Constraints</div>
                <div class="hard-card-text">Aggressive switching reduces stability, so deployment decisions must honor cooldown and lock windows.</div>
            </div>
            <div class="hard-card">
                <div class="hard-card-title">Multi-Objective Optimization</div>
                <div class="hard-card-text">Carbon, latency, and cost pull in different directions, requiring weighted tradeoffs for reliable outcomes.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# CARBON INTENSITY CHART
# ============================================================================

def render_carbon_intensity_chart(data):
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Real-Time Carbon Intensity by Region</h3>', unsafe_allow_html=True)

    fig = go.Figure()

    for region in data['region'].unique():
        region_data = data[data['region'] == region]
        fig.add_trace(go.Scatter(
            x=region_data['timestamp'],
            y=region_data['carbon_intensity'],
            name=f"{region_data['region_flag'].iloc[0]} {region}",
            mode='lines+markers',
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Time: %{x}<br>' +
                         'Carbon: %{y} gCOâ‚‚/kWh<extra></extra>'
        ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#00ffaa', family='Orbitron'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0, 255, 255, 0.1)',
            title='Time',
            title_font=dict(color='#00ffff')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0, 255, 255, 0.1)',
            title='Carbon Intensity (gCOâ‚‚/kWh)',
            title_font=dict(color='#00ffff')
        ),
        hovermode='x unified',
        height=400,
        legend=dict(
            bgcolor='rgba(10, 14, 39, 0.8)',
            bordercolor='rgba(0, 255, 255, 0.3)',
            borderwidth=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# REGION FREQUENCY CHART
# ============================================================================

def render_region_frequency_chart(data):
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Greenest Region Selection Frequency</h3>', unsafe_allow_html=True)

    region_counts = data['region'].value_counts().reset_index()
    region_counts.columns = ['region', 'count']

    # Add flags
    region_flags = {
        'IN': 'ðŸ‡®ðŸ‡³', 'FI': 'ðŸ‡«ðŸ‡®', 'DE': 'ðŸ‡©ðŸ‡ª',
        'JP': 'ðŸ‡¯ðŸ‡µ', 'AU-NSW': 'ðŸ‡¦ðŸ‡º', 'BR-CS': 'ðŸ‡§ðŸ‡·'
    }
    region_counts['display'] = region_counts['region'].map(
        lambda x: f"{region_flags.get(x)} {x}"
    )

    fig = go.Figure(data=[
        go.Bar(
            x=region_counts['display'],
            y=region_counts['count'],
            marker=dict(
                color=region_counts['count'],
                colorscale='Viridis',
                line=dict(color='rgba(0, 255, 255, 0.5)', width=2)
            ),
            text=region_counts['count'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Selections: %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#00ffaa', family='Orbitron'),
        xaxis=dict(
            showgrid=False,
            title='Region',
            title_font=dict(color='#00ffff')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0, 255, 255, 0.1)',
            title='Number of Times Selected',
            title_font=dict(color='#00ffff')
        ),
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SAVINGS GAUGE
# ============================================================================

def render_savings_gauge(savings_percent):
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Carbon Savings Achievement</h3>', unsafe_allow_html=True)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=savings_percent,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Savings %", 'font': {'color': '#00ffff', 'size': 20}},
        delta={'reference': 50, 'increasing': {'color': "#00ff88"}},
        gauge={
            'axis': {'range': [None, 100], 'tickcolor': "#00ffff"},
            'bar': {'color': "#00ff88"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(0, 255, 255, 0.3)",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(255, 0, 102, 0.2)'},
                {'range': [50, 75], 'color': 'rgba(255, 193, 7, 0.2)'},
                {'range': [75, 100], 'color': 'rgba(0, 255, 136, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "#7f00ff", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#00ffaa', family='Orbitron'),
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# LIVE LOGS TABLE
# ============================================================================

def render_logs_table(logs_df):
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Recent Scheduling Decisions</h3>', unsafe_allow_html=True)

    if not logs_df.empty:
        # Format the dataframe for display
        display_df = logs_df.copy()
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # Add status badges
        display_df['status'] = display_df['status'].apply(
            lambda x: 'Success' if x == 'success' else 'Warning'
        )

        st.dataframe(
            display_df[['timestamp', 'region_flag', 'region', 'carbon_intensity',
                       'savings_gco2', 'savings_percent', 'status']],
            use_container_width=True,
            height=400
        )
    else:
        st.info("No decisions logged yet. Trigger the scheduler to see data!")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# PHASE 9: ADVANCED VISUALIZATIONS
# ============================================================================

def render_geographic_map(recent_logs):
    """Render geographic heatmap of regions with carbon intensity"""
    st.markdown('<div class="geo-map-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Global Carbon Intensity Map</h3>', unsafe_allow_html=True)

    # Region coordinates
    region_coords = {
        'IN': {'lat': 20.5937, 'lon': 78.9629, 'name': 'India'},
        'FI': {'lat': 61.9241, 'lon': 25.7482, 'name': 'Finland'},
        'DE': {'lat': 51.1657, 'lon': 10.4515, 'name': 'Germany'},
        'JP': {'lat': 36.2048, 'lon': 138.2529, 'name': 'Japan'},
        'AU-NSW': {'lat': -31.8406, 'lon': 147.3222, 'name': 'Australia (NSW)'},
        'BR-CS': {'lat': -15.8267, 'lon': -47.9218, 'name': 'Brazil (Central-South)'}
    }

    if not recent_logs.empty:
        # Get latest carbon intensity for each region
        latest_data = recent_logs.groupby('region').agg({
            'carbon_intensity': 'last',
            'timestamp': 'last'
        }).reset_index()

        # Create map data
        map_data = []
        for _, row in latest_data.iterrows():
            if row['region'] in region_coords:
                map_data.append({
                    'region': row['region'],
                    'name': region_coords[row['region']]['name'],
                    'lat': region_coords[row['region']]['lat'],
                    'lon': region_coords[row['region']]['lon'],
                    'carbon': row['carbon_intensity'],
                    'size': max(10, 100 - row['carbon_intensity'])  # Invert for visual
                })

        if map_data:
            df_map = pd.DataFrame(map_data)

            fig = px.scatter_geo(df_map,
                lat='lat',
                lon='lon',
                size='size',
                color='carbon',
                hover_name='name',
                hover_data={'carbon': ':.1f', 'lat': False, 'lon': False, 'size': False},
                color_continuous_scale='RdYlGn_r',
                size_max=50,
                labels={'carbon': 'Carbon Intensity (gCOâ‚‚/kWh)'}
            )

            fig.update_layout(
                geo=dict(
                    projection_type='natural earth',
                    showland=True,
                    landcolor='rgb(15, 15, 35)',
                    oceancolor='rgb(10, 10, 25)',
                    showocean=True,
                    showcountries=True,
                    countrycolor='rgb(0, 255, 255, 0.2)',
                    bgcolor='rgba(0,0,0,0)'
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=0, b=0),
                height=400,
                font=dict(color='#00ffaa', family='Orbitron')
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No region data available for map visualization")
    else:
        st.info("No data available - trigger scheduler to see regions")

    st.markdown('</div>', unsafe_allow_html=True)

def render_energy_mix_chart(days=7):
    """Render stacked area chart showing energy mix over time"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="chart-title">Renewable vs Carbon Energy Mix Trend</h3>', unsafe_allow_html=True)

    try:
        energy_mix_data = get_energy_mix_data(days)

        if not energy_mix_data.empty and 'renewable_pct' in energy_mix_data.columns:
            energy_mix_data['fossil_pct'] = 100 - energy_mix_data['renewable_pct']

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=energy_mix_data['timestamp'],
                y=energy_mix_data['renewable_pct'],
                name='Renewable Energy',
                fill='tonexty',
                fillcolor='rgba(0, 255, 136, 0.3)',
                line=dict(color='#00ff88', width=2),
                hovertemplate='%{y:.1f}% Renewable<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=energy_mix_data['timestamp'],
                y=energy_mix_data['fossil_pct'],
                name='Carbon-Based Energy',
                fill='tozeroy',
                fillcolor='rgba(255, 99, 71, 0.3)',
                line=dict(color='#ff6347', width=2),
                hovertemplate='%{y:.1f}% Fossil<extra></extra>'
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ffffff', family='Orbitron'),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(0, 255, 255, 0.1)',
                    title='Time',
                    title_font=dict(color='#00ffaa')
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(0, 255, 255, 0.1)',
                    title='Percentage (%)',
                    title_font=dict(color='#00ffaa'),
                    range=[0, 100]
                ),
                hovermode='x unified',
                height=350,
                margin=dict(l=50, r=20, t=20, b=50),
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='right',
                    x=1,
                    font=dict(color='#ffffff')
                )
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Energy mix data not available - using carbon intensity as proxy")
    except Exception as e:
        st.warning(f"Energy mix visualization unavailable: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


def render_optimal_region_card(
    region,
    score,
    rank,
    total,
    carbon,
    latency,
    cost,
    carbon_quality,
    latency_quality,
    cost_quality,
    weight_carbon,
    weight_latency,
    weight_cost,
    score_advantage_pct,
    stable_hours,
):
    """Render a focused optimal region card for the 2-column optimizer layout."""

    carbon_quality = max(0.0, min(100.0, float(carbon_quality)))
    latency_quality = max(0.0, min(100.0, float(latency_quality)))
    cost_quality = max(0.0, min(100.0, float(cost_quality)))

    st.markdown(f"""
    <div style="background: rgba(21, 31, 67, 0.92);
               border-radius: 16px; padding: 20px; margin-bottom: 14px; min-height: 360px;
               border: 1px solid rgba(0, 212, 255, 0.35);
               text-align: center; display: flex; flex-direction: column; justify-content: center;">
        <div style="font-size: 2rem; font-weight: 700; color: #ffffff; line-height:1.1;">{region}</div>
        <div style="font-size: 0.98rem; color: rgba(255,255,255,0.95); margin-top: 5px;">
            Final Score: <strong>{score:.3f}</strong> | Rank: <strong>#{rank}/{total}</strong>
        </div>
        <div style="margin-top: 12px; display:flex; justify-content: space-between; gap: 8px; text-align:left;">
            <div style="flex:1; background: rgba(255,255,255,0.04); padding:9px; border-radius:10px;">
                <div style="font-size: 0.82rem; color:#95a4c8;">Carbon</div>
                <div style="font-size: 1.08rem; color:#ffffff; font-weight:600;">{carbon:.0f} gCO2/kWh</div>
                <div style="margin-top: 6px; height: 5px; background: rgba(255,255,255,0.12); border-radius: 999px; overflow: hidden;">
                    <div style="width: {carbon_quality:.1f}%; height: 100%; background: linear-gradient(90deg, #35e7a5, #00ffaa);"></div>
                </div>
            </div>
            <div style="flex:1; background: rgba(255,255,255,0.04); padding:9px; border-radius:10px;">
                <div style="font-size: 0.82rem; color:#95a4c8;">Latency</div>
                <div style="font-size: 1.08rem; color:#ffffff; font-weight:600;">{latency:.0f} ms</div>
                <div style="margin-top: 6px; height: 5px; background: rgba(255,255,255,0.12); border-radius: 999px; overflow: hidden;">
                    <div style="width: {latency_quality:.1f}%; height: 100%; background: linear-gradient(90deg, #5dd7ff, #00d4ff);"></div>
                </div>
            </div>
            <div style="flex:1; background: rgba(255,255,255,0.04); padding:9px; border-radius:10px;">
                <div style="font-size: 0.82rem; color:#95a4c8;">Cost</div>
                <div style="font-size: 1.08rem; color:#ffffff; font-weight:600;">${cost:.4f}</div>
                <div style="margin-top: 6px; height: 5px; background: rgba(255,255,255,0.12); border-radius: 999px; overflow: hidden;">
                    <div style="width: {cost_quality:.1f}%; height: 100%; background: linear-gradient(90deg, #b692ff, #9f7aea);"></div>
                </div>
            </div>
        </div>
        <div style="margin-top: 10px; font-size: 0.78rem; color:#9bc8f7;">
            Weighted by: Carbon <strong>{weight_carbon:.0f}%</strong> | Latency <strong>{weight_latency:.0f}%</strong> | Cost <strong>{weight_cost:.0f}%</strong>
        </div>
        <div style="margin-top: 6px; font-size: 0.8rem; color:#d9fbe9;">
            <strong style="color:#52f2a6;">&#10003;</strong> Best overall score (+{score_advantage_pct:.1f}% vs next best region)
        </div>
        <div style="margin-top: 4px; font-size: 0.78rem; color:#9cb4d5;">
            Stable for <strong>{stable_hours:.1f}h</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_deployment_lock_status(logs_df):
    """Render deployment lock timing details from latest scheduler decision."""
    if logs_df is None or logs_df.empty:
        return

    latest = logs_df.sort_values("timestamp", ascending=False).iloc[0]
    last_switched = latest.get("last_switched_hours_ago")
    next_eligible = latest.get("next_eligible_switch_in_hours")
    lock_reason = str(latest.get("switch_reason", "")).replace("_", " ")

    if last_switched is None and next_eligible is None:
        return

    try:
        last_switched = float(last_switched or 0)
        next_eligible = float(next_eligible or 0)
    except (TypeError, ValueError):
        return

    st.markdown(f"""
    <div style="margin-top: 10px; padding: 10px; border-radius: 10px;
                background: rgba(16, 185, 129, 0.10);
                border: 1px solid rgba(16, 185, 129, 0.28);">
        <div style="color:#dffcf4; font-size: 0.82rem; font-weight:600;">Deployment Lock Status</div>
        <div style="color:#bde9ff; font-size: 0.78rem; line-height: 1.5;">
            Last deployed: {last_switched:.2f}h ago | Next eligible switch in: {next_eligible:.2f}h
            <br/>Reason: {lock_reason if lock_reason else 'n/a'}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_region_comparison_chart(df, selected_region):
    """Large comparison chart using grouped bars."""
    selected_mask = df["region"] == selected_region
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Carbon",
        x=df["region"],
        y=df["carbon_norm"],
        marker_color=["#00ffaa" if flag else "rgba(0,255,170,0.35)" for flag in selected_mask],
        customdata=df["carbon_intensity"],
        hovertemplate="<b>%{x}</b><br>Carbon (normalized): %{y:.2f}<br>Raw: %{customdata:.0f} gCOâ‚‚/kWh<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Latency",
        x=df["region"],
        y=df["latency_norm"],
        marker_color=["#00d4ff" if flag else "rgba(0,212,255,0.35)" for flag in selected_mask],
        customdata=df["latency"],
        hovertemplate="<b>%{x}</b><br>Latency (normalized): %{y:.2f}<br>Raw: %{customdata:.0f} ms<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Cost",
        x=df["region"],
        y=df["cost_norm"],
        marker_color=["#9f7aea" if flag else "rgba(159,122,234,0.35)" for flag in selected_mask],
        customdata=df["cost"],
        hovertemplate="<b>%{x}</b><br>Cost (normalized): %{y:.2f}<br>Raw: $%{customdata:.4f}<extra></extra>",
    ))
    fig.update_layout(
        barmode="group",
        title="All Regions Comparison",
        xaxis_title="Regions",
        yaxis_title="Normalized Metric Value",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family="Orbitron", size=10),
        height=360,
        margin=dict(l=36, r=16, t=40, b=54),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)
def render_multi_objective_optimizer(recent_logs=None):
    """Render a minimal 2-column optimizer: optimal card + comparison chart."""
    import streamlit as st
    import pandas as pd

    try:
        st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Optimize Region Selection (Multi-Objective)</div>', unsafe_allow_html=True)

        from predictor import SimplePredictiveScheduler
        scheduler = SimplePredictiveScheduler()

        if "optimization_result" not in st.session_state:
            with st.spinner("Computing optimal region..."):
                st.session_state.optimization_result = scheduler.select_optimal_region(
                    w_carbon=0.5,
                    w_latency=0.3,
                    w_cost=0.2,
                )

        result = st.session_state.get("optimization_result")
        if not result:
            left_col, right_col = st.columns([1, 1], gap="large")
            with left_col:
                st.markdown("#### Optimal Region (Multi-Objective)")
                st.info("Run optimization to see results")
                st.markdown('<div class="skeleton" style="height: 360px;"></div>', unsafe_allow_html=True)
            with right_col:
                st.markdown("#### All Regions Comparison")
                st.info("Run optimization to see results")
                st.markdown('<div class="skeleton" style="height: 360px;"></div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(result.get("all_candidates", []))
        if df.empty:
            left_col, right_col = st.columns([1, 1], gap="large")
            with left_col:
                st.markdown("#### Optimal Region (Multi-Objective)")
                st.info("Run optimization to see results")
            with right_col:
                st.markdown("#### All Regions Comparison")
                st.info("Run optimization to see results")
            return

        # Normalize all metrics to show transparent comparison (lower is better).
        df["carbon_norm"] = (df["carbon_intensity"] - df["carbon_intensity"].min()) / (
            (df["carbon_intensity"].max() - df["carbon_intensity"].min()) or 1
        )
        df["latency_norm"] = (df["latency"] - df["latency"].min()) / (
            (df["latency"].max() - df["latency"].min()) or 1
        )
        df["cost_norm"] = (df["cost"] - df["cost"].min()) / (
            (df["cost"].max() - df["cost"].min()) or 1
        )
        df = df.sort_values("score")

        selected_region = result["region"]
        reset_df = df.reset_index(drop=True)
        selected_rank = int(reset_df.index[reset_df["region"] == selected_region][0]) + 1

        selected_row = reset_df[reset_df["region"] == selected_region].iloc[0]
        carbon_quality = (1 - float(selected_row["carbon_norm"])) * 100
        latency_quality = (1 - float(selected_row["latency_norm"])) * 100
        cost_quality = (1 - float(selected_row["cost_norm"])) * 100

        weights = result.get("weights", {})
        weight_carbon = float(weights.get("carbon", 0.5)) * 100
        weight_latency = float(weights.get("latency", 0.3)) * 100
        weight_cost = float(weights.get("cost", 0.2)) * 100

        score_advantage_pct = 0.0
        if selected_rank == 1 and len(reset_df) > 1:
            next_best_score = float(reset_df.iloc[1]["score"])
            if next_best_score > 0:
                score_advantage_pct = ((next_best_score - float(result["score"])) / next_best_score) * 100

        stable_hours = 0.0
        if recent_logs is not None and not recent_logs.empty:
            latest_row = recent_logs
            if "timestamp" in recent_logs.columns:
                latest_row = recent_logs.sort_values("timestamp", ascending=False)
            latest = latest_row.iloc[0]
            try:
                stable_hours = float(latest.get("last_switched_hours_ago", 0) or 0)
            except (TypeError, ValueError):
                stable_hours = 0.0

        left_col, right_col = st.columns([1, 1], gap="large")

        with left_col:
            st.markdown("#### Optimal Region (Multi-Objective)")
            render_optimal_region_card(
                selected_region,
                result['score'],
                selected_rank,
                len(df),
                result['carbon_intensity'],
                result['latency'],
                result['cost'],
                carbon_quality,
                latency_quality,
                cost_quality,
                weight_carbon,
                weight_latency,
                weight_cost,
                score_advantage_pct,
                stable_hours,
            )

        with right_col:
            st.markdown("#### All Regions Comparison")
            render_region_comparison_chart(df, selected_region)

        render_deployment_lock_status(recent_logs)
    except Exception as e:
        st.error(f" Error in multi-objective optimizer: {str(e)}")


def render_export_section(logs_df):
    """Render data export options"""
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

    with col2:
        if not logs_df.empty:
            csv_data = logs_df.to_csv(index=False)
            st.download_button(
                label="Export CSV",
                data=csv_data,
                file_name=f"cass_lite_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col3:
        if not logs_df.empty:
            json_data = logs_df.to_json(orient='records', date_format='iso', indent=2)
            st.download_button(
                label="Export JSON",
                data=json_data,
                file_name=f"cass_lite_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    st.markdown("""
    <div class="repo-source-card">
        <div class="repo-source-title">Source Repository</div>
        <a class="repo-source-link" href="https://github.com/BharathiSen/cass" target="_blank">View GitHub code</a>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================

def render_footer():
    st.markdown("""
    <div class="footer">
        <p>Built with <span class="footer-icon">&#10084;&#65039;</span> by <strong>Bharathi Senthilkumar</strong></p>
        <p> Powered by Google Cloud </p>
        <p style="font-size: 0.8rem; color: #7f00ff; margin-top: 1rem;">
            Making the cloud greener, one decision at a time
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Auto-refresh disabled to avoid rerender-based switching behavior.

    # Render hero section
    render_hero()

    # Apply high contrast mode if enabled
    apply_high_contrast_css()

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

        theme_toggle = st.checkbox("Dark Mode", value=True)

        st.markdown("---")
        st.markdown("#### Data Range")
        days_filter = st.selectbox("Show last", [1, 3, 7, 14, 30], index=2)

        st.markdown("---")
        st.markdown("#### Quick Actions")

        if st.button("Refresh Data", use_container_width=True):
            st.session_state.data_loading_failed = False
            st.rerun()

        st.markdown("---")
        st.markdown("#### Cloud Run Metrics")

        try:
            # PHASE 9: Display Cloud Run metrics
            st.metric("CPU Usage", "12%", "â†“ 3%")
            st.metric("Memory Usage", "256 MB", "â†‘ 5 MB")
            st.metric("Request Count", "1.2K", "â†‘ 15%")
        except Exception:
            st.info("Metrics loading...")

        st.markdown("---")
        st.markdown("#### Project Info")
        st.markdown("""
        **Project:** CASS-Lite v2
        **Version:** 2.0.0
        **Status:**  Active
        **Region:** asia-south1
        **Cost:** $0.08/month
        """)

    # Fetch data with loading indicators and error handling
    stats = None
    recent_logs = pd.DataFrame()
    region_history = pd.DataFrame()

    try:
        # Show loading spinner while fetching data
        with st.spinner("Loading carbon intelligence data..."):
            # Progress indicator
            progress_bar = st.progress(0)

            # Fetch stats
            progress_bar.progress(25)
            stats = get_summary_stats(days=days_filter)

            # Fetch recent logs
            progress_bar.progress(50)
            recent_logs = fetch_recent_decisions(limit=100)

            # Fetch region history
            progress_bar.progress(75)
            region_history = get_region_history(days=days_filter)

            progress_bar.progress(100)
            time.sleep(0.2)  # Brief pause to show completion
            progress_bar.empty()

            # Mark successful data load
            st.session_state.data_loading_failed = False

    except Exception as e:
        # Display error banner
        st.error(f" Failed to fetch Firestore data: {str(e)}")
        st.warning(" Falling back to mock data for demonstration...")

        # Fallback to mock data
        try:
            with st.spinner("Loading mock data..."):
                stats = get_summary_stats(days=days_filter)
                recent_logs = generate_mock_decisions(100)
                region_history = generate_mock_history(days=days_filter)

            st.session_state.data_loading_failed = True
            st.info("â„¹Displaying mock data. Connect to Firestore for real-time data.")

        except Exception as fallback_error:
            st.error(f"Critical error: {str(fallback_error)}")
            st.stop()

    # Display data status indicator
    if st.session_state.data_loading_failed:
        st.markdown("""
        <div style="background: rgba(255, 193, 7, 0.2);
                    border: 1px solid #ffc107;
                    border-radius: 10px;
                    padding: 10px;
                    margin-bottom: 20px;
                    text-align: center;">
            <span style="color: #ffc107;"> Using Mock Data</span>
        </div>
        """, unsafe_allow_html=True)

    # Render metrics (with skeleton loaders if no data)
    if stats is None or len(recent_logs) == 0:
        # Show skeleton loaders
        st.markdown("### Loading Metrics...")
        col1, col2, col3, col4 = st.columns(4)
        for col in [col1, col2, col3, col4]:
            with col:
                st.markdown('<div class="skeleton" style="height: 150px;"></div>', unsafe_allow_html=True)
    else:
        render_metrics(stats)

    if stats is not None and len(recent_logs) > 0:
        render_impact_metrics_strip(stats, recent_logs)
        render_why_this_is_hard()

    if stats:
        st.markdown("""
        <div style="margin-top: 16px; margin-bottom: 12px; padding: 14px 16px;
                    border-radius: 12px;
                    border: 1px solid rgba(0, 255, 255, 0.25);
                    background: rgba(0, 255, 255, 0.06);">
            <div style="font-size: 0.88rem; color: #8dd3ff; text-transform: uppercase; font-weight: 700; margin-bottom: 8px;">
                Stable Decision Policy
            </div>
            <div style="font-size: 0.95rem; color: #d8efff;">
                Decision based on <strong>24h average</strong> |
                Last switched: <strong>{last_switched:.2f}h ago</strong> |
                Next eligible switch in: <strong>{next_eligible:.2f}h</strong> |
                Reason: <strong>{reason}</strong>
            </div>
        </div>
        """.format(
            last_switched=float(stats.get('last_switched_hours_ago', 0)),
            next_eligible=float(stats.get('next_eligible_switch_in_hours', 0)),
            reason=str(stats.get('switch_reason', 'n/a')).replace('_', ' ')
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two column layout for charts
    col1, col2 = st.columns([2, 1])

    with col1:
        if region_history.empty:
            st.markdown("### Carbon Intensity Over Time")
            st.markdown('<div class="skeleton" style="height: 400px;"></div>', unsafe_allow_html=True)
        else:
            render_carbon_intensity_chart(region_history)

    with col2:
        if stats:
            render_savings_gauge(stats.get('savings_percent', 0))
        else:
            st.markdown("### Carbon Savings")
            st.markdown('<div class="skeleton" style="height: 300px;"></div>', unsafe_allow_html=True)

    # PHASE 9: Geographic Map
    if not recent_logs.empty:
        render_geographic_map(recent_logs)
    else:
        st.markdown("### Global Carbon Intensity Map")
        st.markdown('<div class="skeleton" style="height: 500px;"></div>', unsafe_allow_html=True)

    # Two column layout for advanced charts
    col3, col4 = st.columns(2)

    with col3:
        # Region frequency chart
        if not recent_logs.empty:
            render_region_frequency_chart(recent_logs)
        else:
            st.markdown("### Region Selection Frequency")
            st.markdown('<div class="skeleton" style="height: 400px;"></div>', unsafe_allow_html=True)

    with col4:
        # PHASE 9: Energy mix chart
        render_energy_mix_chart(days=days_filter)

    # Multi-Objective Optimization Section
    render_multi_objective_optimizer(recent_logs=recent_logs)

    # Live logs table
    render_logs_table(recent_logs)

    # PHASE 9: Export Section
    if not recent_logs.empty:
        render_export_section(recent_logs)

    # Footer
    render_footer()

    # PHASE 9: Refresh Indicator (bottom-right)
    st.markdown("""
    <div class="refresh-indicator">
        <div class="pulse"></div>
        <span style="margin-left: 8px; font-size: 0.8rem;">Live</span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()



