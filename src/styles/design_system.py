import streamlit as st

def apply_custom_css():
    """Apply a Premium Dark SaaS (Obsidian & Emerald) design system."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');

        :root {
            --bg-primary: #0A0A0A;
            --bg-secondary: #0F0F0F;
            --bg-input: #1A1A1A;
            --accent-green: #10B981;
            --accent-blue: #3B82F6;
            --text-main: #F9FAFB;
            --text-secondary: #9CA3AF;
            --border-color: rgba(255, 255, 255, 0.08);
            --card-glass: rgba(20, 20, 20, 0.7);
        }

        /* Global Reset & Typography */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
            background-color: var(--bg-primary) !important;
            font-family: 'Inter', sans-serif !important;
            color: var(--text-main);
        }
        
        /* Remove the annoying blue header bar */
        header { 
            background-color: var(--bg-primary) !important; 
            border-bottom: 1px solid var(--border-color);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-secondary) !important;
            border-right: 1px solid var(--border-color);
        }

        /* Input / Widget Backgrounds */
        div[data-baseweb="select"] > div, 
        div[data-baseweb="input"] > div,
        .stSelectbox div, .stMultiSelect div {
            background-color: var(--bg-input) !important;
            border-color: var(--border-color) !important;
            color: white !important;
        }

        /* Hero Styling */
        .hero-header {
            padding: 4rem 2rem 2rem 2rem;
            text-align: center;
            background: radial-gradient(circle at top, rgba(16, 185, 129, 0.08) 0%, transparent 70%);
        }

        .hero-title {
            font-family: 'Outfit', sans-serif !important;
            font-size: 3.5rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.04em !important;
            background: linear-gradient(to bottom right, #FFFFFF 30%, #9CA3AF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem !important;
        }

        /* Bento Metric Cards */
        .metric-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            border-color: var(--accent-green);
        }

        .metric-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.5rem;
        }

        /* Section Titles */
        .section-title {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.25rem;
            font-weight: 600;
            color: white;
            margin: 3rem 0 1.5rem 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .section-title::before {
            content: '';
            width: 3px;
            height: 18px;
            background: var(--accent-green);
            border-radius: 2px;
        }

        /* Chart Containers */
        .chart-container {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* Footer & Export Area */
        .export-container {
            margin-top: 4rem;
            padding: 3rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_high_contrast_css():
    st.markdown("""
    <style>
        :root { --bg-primary: #000; --text-main: #fff; --accent-green: #0f0; }
    </style>
    """, unsafe_allow_html=True)
