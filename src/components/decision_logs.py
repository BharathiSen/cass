import streamlit as st
import pandas as pd

REGION_FLAGS = {
    'IN': '🇮🇳 India',
    'FI': '🇫🇮 Finland',
    'DE': '🇩🇪 Germany',
    'JP': '🇯🇵 Japan',
    'AU-NSW': '🇦🇺 Australia',
    'BR-CS': '🇧🇷 Brazil'
}

def render_decision_log_stable(logs_df):
    """Bulletproof HTML Audit Table with CSV & JSON export."""
    st.markdown('<div class="chart-container" style="padding:0;">', unsafe_allow_html=True)
    st.markdown('<div style="padding:1.5rem; font-weight:600; font-size:1.1rem;">Live Decision Audit Log</div>', unsafe_allow_html=True)

    if not logs_df.empty:
        df = logs_df.copy().head(10)

        # Safe column fallback for region and carbon
        for fallback_col in ['region', 'timestamp', 'carbon_intensity']:
            if fallback_col not in df.columns:
                df[fallback_col] = pd.NaT if fallback_col == 'timestamp' else ('N/A' if fallback_col == 'region' else 0)

        # Map status appropriately from execution_success if available
        if 'execution_success' in df.columns:
            df['status'] = df['execution_success'].map({True: 'success', False: 'failed'}).fillna('unknown')
        elif 'status' not in df.columns:
            df['status'] = 'unknown'
        else:
            df['status'] = df['status'].fillna('unknown')

        parsed_ts = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce', utc=True)
        df['time'] = parsed_ts.dt.strftime('%H:%M:%S').fillna('N/A')

        # Fill missing regions to prevent display gaps
        df['region'] = df['region'].fillna('N/A')
        df['flag'] = df['region'].map(REGION_FLAGS).fillna(df['region'])

        # HTML Table
        html_table = df[['time', 'flag', 'carbon_intensity', 'status']].rename(
            columns={'time': 'Time', 'flag': 'Region', 'carbon_intensity': 'Carbon (gCO₂/kWh)', 'status': 'Status'}
        ).to_html(classes='table table-dark', index=False, justify='center', border=0)
        st.markdown(
            f'<div style="max-height:400px; overflow-y:auto; padding:0 1.5rem 1rem 1.5rem;">{html_table}</div>',
            unsafe_allow_html=True
        )

        # --- Export Buttons ---
        st.markdown('<div style="padding:0 1.5rem 1.5rem 1.5rem;">', unsafe_allow_html=True)

        # Build export dataframe
        export_df = logs_df.copy()
        for col, default in [('timestamp', pd.NaT), ('carbon_intensity', 0), ('status', 'unknown')]:
            if col not in export_df.columns:
                export_df[col] = default

        export_df = export_df[['timestamp', 'carbon_intensity', 'status']].rename(
            columns={'timestamp': 'Timestamp', 'carbon_intensity': 'Carbon_gCO2_kWh', 'status': 'Status'}
        )

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download Audit as CSV",
                data=export_df.to_csv(index=False).encode('utf-8'),
                file_name="cass_audit_log.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="⬇️ Download Audit as JSON",
                data=export_df.to_json(orient='records', indent=2).encode('utf-8'),
                file_name="cass_audit_log.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def render_multi_objective_optimizer(recent_logs=None): pass
def render_why_this_is_hard(): pass
def render_results_section(stats, recent_logs): pass
def render_engineering_decisions(): pass
def render_export_section(df): pass
