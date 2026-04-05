import streamlit as st

def render_metrics(stats):
    """Bento-style metric cards for core performance indicators."""
    col1, col2, col3, col4 = st.columns(4)

    if not stats or stats.get('total_decisions', 0) == 0:
        for col in [col1, col2, col3, col4]:
            with col: st.markdown('<div class="skeleton" style="height: 140px; border-radius: 16px; background: rgba(255,255,255,0.02);"></div>', unsafe_allow_html=True)
        return

    savings_percent = stats.get('savings_percent', 0)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Grid Intensity</div>
            <div class="metric-value">{stats.get('avg_carbon', 0):.0f}</div>
            <div class="metric-delta">gCO₂/kWh (Global)</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-bottom: 2px solid var(--accent-green);">
            <div class="metric-label">Optimization Gain</div>
            <div class="metric-value">-{savings_percent:.1f}%</div>
            <div class="metric-delta" style="color:#10B981; font-weight:600;">CO₂ Avoided</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Policy Status</div>
            <div class="metric-value">Active</div>
            <div class="metric-delta" style="color:var(--accent-blue);">{stats.get('greenest_region', 'N/A')} is Greenest</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">System Audit</div>
            <div class="metric-value">{stats.get('total_decisions', 0)}</div>
            <div class="metric-delta">Decisions Polled</div>
        </div>
        """, unsafe_allow_html=True)

def render_impact_metrics_strip(stats, recent_logs):
    """Auxiliary impact KPIs (placeholder for future expansion)."""
    pass

def render_slo_cards(slo_snapshot):
    """System-level objectives summary."""
    if not slo_snapshot or not slo_snapshot.get('available'): return
    
    comp = slo_snapshot.get('compliance', {})
    status = "SUCCESS" if comp.get('all_met') else "AT RISK"
    color = "#10B981" if comp.get('all_met') else "#EF4444"

    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:12px; padding:16px; margin: 16px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
             <div style="font-weight:600; font-size:0.875rem; color:{color};">● SLO STATUS: {status}</div>
             <div style="font-size:0.75rem; color:var(--text-secondary);">Last 72h Performance Window</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
