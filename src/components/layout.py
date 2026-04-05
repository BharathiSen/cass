import streamlit as st
from datetime import datetime

def render_hero():
    """Clean, high-typography hero section."""
    st.markdown("""
    <div style="padding: 2.5rem 2rem 1.5rem 2rem; text-align: center; background: radial-gradient(circle at top, rgba(16, 185, 129, 0.08) 0%, transparent 70%);">
        <span style="display:block; font-size: 3.5rem; font-weight: 700; letter-spacing: -0.04em; color: #FFFFFF !important; margin-bottom: 0.75rem; font-family: sans-serif; line-height: 1.1;">CASS-Lite v2</span>
        <span style="display:block; color: #9CA3AF; font-size: 1.05rem; max-width: 650px; margin: 0 auto; line-height: 1.6;">
            Autonomous multi-objective cloud orchestration reducing global carbon footprint through real-time grid intelligence.
        </span>
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
