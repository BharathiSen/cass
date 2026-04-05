import streamlit as st
import pandas as pd

def render_decision_log_stable(logs_df):
    """Stable HTML Audit Table (Bypasses Streamlit Data Engine Bug)."""
    st.markdown('<div class="chart-container" style="padding:0;">', unsafe_allow_html=True)
    st.markdown('<div style="padding:1.5rem; font-weight:600; font-size:1.1rem;">Live Decision Audit Log</div>', unsafe_allow_html=True)
    if not logs_df.empty:
        df = logs_df.copy().head(10)
        df['time'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
        
        # Custom HTML Table for maximum stability and Obsidian styling
        html_table = df[['time', 'region', 'carbon_intensity', 'status']].to_html(
            classes='table table-dark', index=False, justify='center', border=0
        )
        st.markdown(f'<div style="max-height: 400px; overflow-y: auto; padding: 0 1.5rem 1.5rem 1.5rem;">{html_table}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_multi_objective_optimizer(recent_logs=None): pass
def render_why_this_is_hard(): pass
def render_results_section(stats, recent_logs): pass
def render_engineering_decisions(): pass
def render_export_section(df): pass
