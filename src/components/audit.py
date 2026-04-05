import streamlit as st
import pandas as pd

def render_logs_table(logs_df):
    """Audit Table for real-time orchestration decisions."""
    st.markdown('<div class="chart-container" style="padding:0;">', unsafe_allow_html=True)
    st.markdown('<div style="padding:1.5rem; font-weight:600; font-size:1.1rem;">Live Decision Audit Log</div>', unsafe_allow_html=True)
    if not logs_df.empty:
        df = logs_df.copy().head(10)
        df['time'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
        st.dataframe(df[['time', 'region', 'carbon_intensity', 'status']], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_export_section(logs_df):
    """Data Download Section for recruiters/auditors."""
    if logs_df.empty: return
    
    st.markdown('<div class="section-title">Operations Data Export</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        csv = logs_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download as CSV (Audit Ready)", data=csv, file_name='cass_audit_log.csv', mime='text/csv', use_container_width=True)
    with col2:
        json_data = logs_df.to_json(orient='records', indent=2).encode('utf-8')
        st.download_button(label="Download as JSON (Automation Ready)", data=json_data, file_name='cass_audit_log.json', mime='application/json', use_container_width=True)

def render_engineering_decisions():
    """Information regarding the systems thinking and decisions."""
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 20px; padding: 2rem; margin-top: 2rem; margin-bottom: 3rem;">
        <h3 style="font-family:'Outfit'; font-size:1.25rem; margin-bottom: 1.5rem;">CASS Decision Engine Methodology</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem;">
            <div>
                <p style="color:var(--accent-green); font-weight:600; margin-bottom:0.5rem; font-size:0.875rem;">1. Grid Polling</p>
                <p style="font-size:0.825rem; color:var(--text-secondary);">Real-time tracking across 6 global zones with polling intervals mapped to grid volatility.</p>
            </div>
            <div>
                <p style="color:var(--accent-blue); font-weight:600; margin-bottom:0.5rem; font-size:0.875rem;">2. Weighted Strategy</p>
                <p style="font-size:0.825rem; color:var(--text-secondary);">Proprietary composite scoring balancing CO₂ reduction vs cross-region network latency costs.</p>
            </div>
            <div>
                <p style="color:#A855F7; font-weight:600; margin-bottom:0.5rem; font-size:0.875rem;">3. Cold-Migration Lock</p>
                <p style="font-size:0.825rem; color:var(--text-secondary);">Strict 24h cooldown prevents thrashing and stabilizes compute workloads during grid spikes.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_multi_objective_optimizer(recent_logs=None): pass
def render_why_this_is_hard(): pass
def render_results_section(stats, recent_logs): pass
