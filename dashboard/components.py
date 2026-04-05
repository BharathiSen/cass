import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Simple Regional Map Data (Local)
REGION_MAP_DATA = {
    'IN': {'lat': 20.5937, 'lon': 78.9629, 'name': 'India (asia-south1)'},
    'FI': {'lat': 61.9241, 'lon': 25.7482, 'name': 'Finland (europe-north1)'},
    'DE': {'lat': 51.1657, 'lon': 10.4515, 'name': 'Germany (europe-west3)'},
    'JP': {'lat': 36.2048, 'lon': 138.2529, 'name': 'Japan (asia-northeast1)'},
    'AU-NSW': {'lat': -31.8406, 'lon': 147.3222, 'name': 'Australia (australia-southeast1)'},
    'BR-CS': {'lat': -15.8267, 'lon': -47.9218, 'name': 'Brazil (southamerica-east1)'}
}

def render_hero():
    """Simple Hero section."""
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">CASS-Lite v2</h1>
        <p style="color:var(--text-secondary); max-width:600px; margin:0 auto; font-size:1.1rem; font-weight:400; line-height:1.6;">
            Autonomous multi-objective cloud orchestration reducing global carbon footprint through real-time grid intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_system_status(status_msg):
    """Matching the yellow alert bar in your screenshot."""
    st.warning(f"⚠️ {status_msg}")

def render_metrics(stats):
    """Bento metrics with the exact labels and highlight colors from your screenshot."""
    col1, col2, col3, col4 = st.columns(4)
    if not stats: return

    savings_percent = stats.get('savings_percent', 0)
    green_reg = stats.get('greenest_region', 'N/A')
    total_decisions = stats.get('total_decisions', 0)
    avg_carbon = stats.get('avg_carbon', 0)
    
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">AVG GRID INTENSITY</div><div class="metric-value">{avg_carbon:.0f}</div><div class="metric-delta">gCO₂/kWh (Global)</div></div>""", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""<div class="metric-card" style="border-bottom: 2px solid var(--accent-green);"><div class="metric-label">OPTIMIZATION GAIN</div><div class="metric-value" style="color: var(--accent-green);">-{savings_percent:.1f}%</div><div class="metric-delta" style="color: var(--accent-green); font-weight:500;">CO₂ Avoided</div></div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">POLICY STATUS</div><div class="metric-value">Active</div><div class="metric-delta" style="color: var(--accent-blue); font-weight:500;">{green_reg} is Greenest</div></div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">SYSTEM AUDIT</div><div class="metric-value">{total_decisions}</div><div class="metric-delta">Decisions Polled</div></div>""", unsafe_allow_html=True)

def render_slo_strip():
    """Matching the SLO strip in your screenshot."""
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.25rem; margin-top: 2rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
             <div style="color:#10B981; font-weight:600; font-size:0.75rem;"><span style="margin-right:8px;">●</span>SLO STATUS: SUCCESS</div>
             <div style="color:var(--text-secondary); font-size:0.7rem; font-weight:500; text-transform:uppercase; letter-spacing:0.04em;">Last 72h Performance Window</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_geographic_map(recent_logs): 
    """Global Observability Map."""
    st.markdown('<div class="chart-container"><div style="font-weight:600; font-size:1.1rem; margin-bottom:1.5rem;">Global Infrastructure Carbon Heatmap</div>', unsafe_allow_html=True)
    if not recent_logs.empty:
        map_df_list = []
        for zone, coord in REGION_MAP_DATA.items():
            reg_logs = recent_logs[recent_logs['region'] == zone]
            carbon = reg_logs['carbon_intensity'].iloc[0] if not reg_logs.empty else 250
            map_df_list.append({'region': zone, 'name': coord['name'], 'lat': coord['lat'], 'lon': coord['lon'], 'carbon': carbon, 'Size': 20})
        
        fig = px.scatter_geo(pd.DataFrame(map_df_list), lat="lat", lon="lon", hover_name="name", size="Size", color="carbon", color_continuous_scale="RdYlGn_r", projection="natural earth")
        fig.update_layout(geo=dict(showland=True, landcolor="#1A1A1A", showocean=True, oceancolor="#000000", showcountries=True, countrycolor="#333333", bgcolor="rgba(0,0,0,0)", framecolor="rgba(0,0,0,0)"), paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0), height=450, font=dict(family="Inter", color="white"))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_carbon_intensity_chart(data):
    """Regional grid trends."""
    st.markdown('<div class="chart-container"><div style="font-weight:600; font-size:1.1rem; margin-bottom:1.5rem;">Real-Time Emission Telemetry</div>', unsafe_allow_html=True)
    if not data.empty:
        fig = go.Figure()
        for region in data['region'].unique():
            reg_data = data[data['region'] == region]
            fig.add_trace(go.Scatter(x=reg_data['timestamp'], y=reg_data['carbon_intensity'], name=f"{region}", mode='lines', line=dict(width=1.5)))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9CA3AF', family='Inter'), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), height=320, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_savings_gauge(percent):
    """Optimization efficiency ring gauge."""
    st.markdown('<div class="chart-container"><div style="text-align:center; font-weight:600; font-size:1.1rem; margin-bottom:1rem;">Optimization Efficiency</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(mode="gauge+number", value=percent, number={'suffix': "%", 'font': {'size': 48, 'family': 'Outfit'}}, gauge={'axis': {'range': [None, 100], 'tickwidth': 1}, 'bar': {'color': "#10B981"}, 'bgcolor': "rgba(255,255,255,0.05)"}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(l=30, r=30, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_footer():
    """Branded project footer."""
    st.markdown(f"""<div style="margin-top: 5rem; padding: 3rem 0; text-align: center; color: var(--text-secondary); font-size: 0.8125rem;"><p>© {datetime.now().year} · Carbon-Aware Cloud Orchestrator by Bharathi Senthilkumar</p><p style="margin-top:0.5rem; font-weight: 500; color: var(--accent-green);">Optimized for Green Infrastructure.</p></div>""", unsafe_allow_html=True)

def render_export_section(df):
    """Download center for recruiter review."""
    st.markdown('<div class="section-title">Operations Data Export</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: st.download_button("Download Audit (CSV)", df.to_csv(index=False).encode('utf-8'), "audit_log.csv", "text/csv", use_container_width=True)
    with col2: st.download_button("Download Audit (JSON)", df.to_json(orient='records').encode('utf-8'), "audit_log.json", "application/json", use_container_width=True)

# Engineering Insights Tab
def render_engineering_insights():
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 20px; padding: 2rem; margin-top: 2rem;">
        <h3 style="font-family:'Outfit'; font-size:1.25rem; margin-bottom: 1.5rem;">CASS Decision Engine Methodology</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem;">
            <div>
                <p style="color:var(--accent-green); font-weight:600; margin-bottom:0.5rem; font-size:0.875rem;">1. Grid Polling</p>
                <p style="font-size:0.825rem; color:var(--text-secondary);">Real-time tracking across global zones with frequency mapping to grid volatility.</p>
            </div>
            <div>
                <p style="color:var(--accent-blue); font-weight:600; margin-bottom:0.5rem; font-size:0.875rem;">2. Weighted Strategy</p>
                <p style="font-size:0.825rem; color:var(--text-secondary);">Proprietary scoring balancing carbon reduction vs network latency costs.</p>
            </div>
            <div>
                <p style="color:#A855F7; font-weight:600; margin-bottom:0.5rem; font-size:0.875rem;">3. Stability Lock</p>
                <p style="font-size:0.825rem; color:var(--text-secondary);">Strict 24h cooldown triggers prevent deployment thrashing and stabilize state.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Compatibility wrappers
def render_impact_metrics_strip(s, l): pass
def render_why_this_is_hard(): pass
def render_results_section(s, l): pass
def render_logs_table(l): pass
def render_region_frequency_chart(l): pass
def render_energy_mix_chart(d): pass
def render_multi_objective_optimizer(l): pass
