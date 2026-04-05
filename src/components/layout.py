import streamlit as st
from datetime import datetime

def render_hero():
    """Clean, high-typography hero section."""
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">CASS-Lite v2</h1>
        <p class="hero-subtitle">
            Autonomous multi-objective cloud orchestration reducing global carbon footprint through real-time grid intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Project-branded footer with focus on sustainability."""
    st.markdown(f"""
    <div style="margin-top: 5rem; padding: 3rem 0; text-align: center; color: var(--text-secondary); font-size: 0.8125rem;">
        <p>© {datetime.now().year} · Carbon-Aware Cloud Orchestrator by Bharathi Senthilkumar</p>
        <p style="margin-top:0.5rem; font-weight: 500; color: var(--accent-green);">Optimized for Green Infrastructure.</p>
    </div>
    """, unsafe_allow_html=True)
