import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Region coordinates for the Global Map
REGION_MAP_DATA = {
    'IN': {'lat': 20.5937, 'lon': 78.9629, 'name': 'India (asia-south1)'},
    'FI': {'lat': 61.9241, 'lon': 25.7482, 'name': 'Finland (europe-north1)'},
    'DE': {'lat': 51.1657, 'lon': 10.4515, 'name': 'Germany (europe-west3)'},
    'JP': {'lat': 36.2048, 'lon': 138.2529, 'name': 'Japan (asia-northeast1)'},
    'AU-NSW': {'lat': -31.8406, 'lon': 147.3222, 'name': 'Australia (australia-southeast1)'},
    'BR-CS': {'lat': -15.8267, 'lon': -47.9218, 'name': 'Brazil (southamerica-east1)'}
}

def render_geographic_map(recent_logs): 
    """High-end Global Carbon Observability Map."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:600; font-size:1.1rem; margin-bottom:1.5rem;">Global Infrastructure Carbon Heatmap</div>', unsafe_allow_html=True)
    
    if not recent_logs.empty:
        # Aggregate data for map
        map_df_list = []
        for zone, coord in REGION_MAP_DATA.items():
            reg_logs = recent_logs[recent_logs['region'] == zone]
            carbon = reg_logs['carbon_intensity'].iloc[0] if not reg_logs.empty else 250
            map_df_list.append({
                'region': zone,
                'name': coord['name'],
                'lat': coord['lat'],
                'lon': coord['lon'],
                'carbon': carbon,
                'Size': 20
            })
        
        fig = px.scatter_geo(
            pd.DataFrame(map_df_list),
            lat="lat", lon="lon",
            hover_name="name",
            size="Size",
            color="carbon",
            color_continuous_scale="RdYlGn_r",
            projection="natural earth",
        )

        fig.update_layout(
            geo=dict(
                showland=True, landcolor="#1A1A1A",
                showocean=True, oceancolor="#000000",
                showcountries=True, countrycolor="#333333",
                bgcolor="rgba(0,0,0,0)",
                framecolor="rgba(0,0,0,0)"
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=450,
            font=dict(family="Inter", color="white")
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Awaiting telemetry data...")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_carbon_intensity_chart(data):
    """Time-series visualization of grid emissions."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:600; font-size:1.1rem; margin-bottom:1.5rem;">Real-Time Emission Telemetry</div>', unsafe_allow_html=True)
    
    if data.empty: return

    fig = go.Figure()
    for region in data['region'].unique():
        reg_data = data[data['region'] == region]
        fig.add_trace(go.Scatter(x=reg_data['timestamp'], y=reg_data['carbon_intensity'], name=f"{region}", mode='lines', line=dict(width=1.5)))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9CA3AF', family='Inter'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        height=320, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_savings_gauge(savings_percent):
    """Efficiency Ring Gauge."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; font-weight:600; font-size:1.1rem; margin-bottom:1rem;">Optimization Efficiency</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = savings_percent,
        number = {'suffix': "%", 'font': {'size': 48, 'family': 'Outfit'}},
        gauge = {'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#333"}, 'bar': {'color': "#10B981"}, 'bgcolor': "rgba(255,255,255,0.05)", 'borderwidth': 0}
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(l=30, r=30, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_region_frequency_chart(data): pass
def render_energy_mix_chart(days=7): pass
