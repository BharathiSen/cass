def render_multi_objective_optimizer():
    """
    Render Multi-Objective Optimization Section - Clean 3-column layout
    """
    import streamlit as st
    import pandas as pd
    import plotly.graph_objects as go

    st.markdown('<div class="neon-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Optimize Region Selection</div>', unsafe_allow_html=True)

    try:
        from predictor import SimplePredictiveScheduler
        scheduler = SimplePredictiveScheduler()

        # Single Live Mode badge - bottom right only
        data_mode = "live-mode" if not st.session_state.data_loading_failed else "simulated-mode"
        data_mode_text = "Live Mode" if not st.session_state.data_loading_failed else "Simulated Mode"
        
        st.markdown(f"""
        <div class="floating-badge {data_mode}">
            {data_mode_text}
        </div>
        """, unsafe_allow_html=True)

        # CLEAN 3-COLUMN LAYOUT - NO EXTRA CONTAINERS
        col1, col2, col3 = st.columns([1.3, 1, 1.2])

        # ===== COLUMN 1: OBJECTIVE WEIGHTS =====
        with col1:
            st.markdown("#### Objective Weights")
            
            w_carbon = st.slider("Carbon Weight", 0.0, 1.0, 0.5, 0.1,
                               help="Higher values prioritize lower carbon intensity")
            w_latency = st.slider("Latency Weight", 0.0, 1.0, 0.3, 0.1,
                                help="Higher values prioritize lower network latency")
            w_cost = st.slider("Cost Weight", 0.0, 1.0, 0.2, 0.1,
                             help="Higher values prioritize lower regional costs")

            # Normalized weights
            total = w_carbon + w_latency + w_cost
            if total > 0:
                norm_carbon = (w_carbon / total) * 100
                norm_latency = (w_latency / total) * 100
                norm_cost = (w_cost / total) * 100

                st.markdown(f"""
                <div style="margin-top: 20px; padding: 15px; background: rgba(127, 0, 255, 0.15);
                           border-radius: 10px; border: 1px solid rgba(127, 0, 255, 0.3);">
                    <div style="font-size: 0.85rem; color: #00ffaa; margin-bottom: 10px; font-weight: 600;">
                        Normalized Weights:
                    </div>
                    <div style="font-size: 1.05rem; color: #00d4ff; font-weight: 600;">
                         {norm_carbon:.1f}% |  {norm_latency:.1f}% |  {norm_cost:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div style="margin-top: 15px; padding: 10px; background: rgba(0, 212, 255, 0.1);
                       border-radius: 8px; font-size: 0.8rem; border: 1px solid rgba(0, 212, 255, 0.2);">
                 Using real-time carbon intensity data
            </div>
            """, unsafe_allow_html=True)

            if st.button(" Optimize Region Selection", type="primary", use_container_width=True):
                with st.spinner("Computing optimal region..."):
                    result = scheduler.select_optimal_region(w_carbon=w_carbon, w_latency=w_latency, w_cost=w_cost)
                    if result['success']:
                        st.session_state.optimization_result = result
                    else:
                        st.error(f" Optimization failed: {result.get('error', 'Unknown error')}")

        # ===== COLUMN 2: OPTIMAL REGION =====
        with col2:
            if 'optimization_result' in st.session_state:
                result = st.session_state.optimization_result
                st.markdown("#### Optimal Region")

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #7f00ff, #00d4ff); border-radius: 15px;
                           padding: 25px; margin-bottom: 15px; text-align: center;
                           box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3);">
                    <div style="font-size: 2.2rem; font-weight: bold; color: white; margin-bottom: 10px;
                               font-family: 'Orbitron', monospace;">{result['region']}</div>
                    <div style="font-size: 1rem; color: rgba(255,255,255,0.95);">
                        Score: <strong style="font-size: 1.2rem;">{result['score']:.3f}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.metric("Carbon", f"{result['carbon_intensity']:.0f} gCO₂/kWh",
                         f"{result['savings_gco2']:.0f} saved" if result['savings_gco2'] > 0 else None)
                st.metric("Latency", f"{result['latency']}ms", "Estimated")
                st.metric("Cost", f"${result['cost']:.4f}", "per vCPU-hour")
            else:
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: center; height: 300px;
                           text-align: center; color: #b0b0b0;">
                    <div>
                        <div style="font-size: 3rem; margin-bottom: 15px;"></div>
                        <div style="font-size: 0.95rem;">
                            Adjust weights and click<br/><strong>Optimize Region Selection</strong>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ===== COLUMN 3: ALL CANDIDATES COMPARISON =====
        with col3:
            if 'optimization_result' in st.session_state:
                result = st.session_state.optimization_result
                st.markdown("#### All Candidates Comparison")

                candidates_df = pd.DataFrame(result['all_candidates']).sort_values('score')

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=candidates_df['region'], y=candidates_df['score'],
                    text=candidates_df['score'].apply(lambda x: f'{x:.3f}'), textposition='outside',
                    marker=dict(color=candidates_df['score'], colorscale='Viridis_r', showscale=False)
                ))
                fig.update_layout(
                    xaxis_title="", yaxis_title="Score",
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Orbitron', size=10), height=320,
                    margin=dict(l=40, r=20, t=20, b=40),
                    xaxis=dict(tickangle=-45, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: center; height: 300px;
                           text-align: center; color: #b0b0b0;">
                    <div>
                        <div style="font-size: 3rem; margin-bottom: 15px;"></div>
                        <div style="font-size: 0.95rem;">Comparison chart<br/>will appear here</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # PARETO FRONTIER - Full width below (only after optimization)
        if 'optimization_result' in st.session_state:
            result = st.session_state.optimization_result
            st.markdown('<div class="neon-divider" style="margin-top: 30px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Pareto Frontier</div>', unsafe_allow_html=True)

            pareto_points = scheduler.generate_pareto_frontier(objective1='carbon', objective2='latency')
            if pareto_points:
                all_points_df = pd.DataFrame(result['all_candidates'])
                pareto_df = pd.DataFrame(pareto_points)

                fig_pareto = go.Figure()
                fig_pareto.add_trace(go.Scatter(
                    x=all_points_df['carbon_intensity'], y=all_points_df['latency'], mode='markers',
                    name='All Regions', marker=dict(size=12, color='rgba(127, 0, 255, 0.5)'),
                    text=all_points_df['region'],
                    hovertemplate='<b>%{text}</b><br>Carbon: %{x:.0f} gCO₂/kWh<br>Latency: %{y}ms<extra></extra>'
                ))
                fig_pareto.add_trace(go.Scatter(
                    x=pareto_df['carbon'], y=pareto_df['latency'], mode='lines+markers',
                    name='Pareto Frontier', line=dict(color='#00d4ff', width=3),
                    marker=dict(size=15, color='#00d4ff', symbol='star'), text=pareto_df['region'],
                    hovertemplate='<b>%{text}</b><br>Carbon: %{x:.0f} gCO₂/kWh<br>Latency: %{y}ms<extra></extra>'
                ))
                selected_row = all_points_df[all_points_df['region'] == result['region']].iloc[0]
                fig_pareto.add_trace(go.Scatter(
                    x=[selected_row['carbon_intensity']], y=[selected_row['latency']], mode='markers',
                    name='Selected', marker=dict(size=20, color='#ff00ff', symbol='diamond', line=dict(color='white', width=2)),
                    hovertemplate=f"<b>{result['region']} (Selected)</b><br>Carbon: {selected_row['carbon_intensity']:.0f} gCO₂/kWh<br>Latency: {selected_row['latency']}ms<extra></extra>"
                ))
                fig_pareto.update_layout(
                    title=dict(text="Carbon Intensity vs Network Latency", font=dict(size=16, color='white', family='Orbitron')),
                    xaxis_title="Carbon Intensity (gCO₂/kWh)", yaxis_title="Network Latency (ms)",
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Orbitron'), height=450, hovermode='closest', showlegend=True,
                    legend=dict(x=0.98, y=0.98, xanchor='right', yanchor='top', bgcolor='rgba(0,0,0,0.7)',
                              bordercolor='rgba(0, 212, 255, 0.5)', borderwidth=2),
                    xaxis=dict(gridcolor='rgba(0, 212, 255, 0.1)', showgrid=True),
                    yaxis=dict(gridcolor='rgba(0, 212, 255, 0.1)', showgrid=True)
                )
                st.plotly_chart(fig_pareto, use_container_width=True)

                st.markdown("""
                <div style="background: rgba(127, 0, 255, 0.1); border-radius: 10px; padding: 15px; margin-top: 15px;
                           border: 1px solid rgba(127, 0, 255, 0.2);">
                    <p style="color: #b0b0b0; font-size: 0.9rem; margin: 0;">
                        <strong style="color: #00ffaa;"> Pareto Frontier:</strong> Regions on the frontier represent optimal trade-offs.
                        No region can improve one objective without worsening another.
                    </p>
                </div>
                """, unsafe_allow_html=True)

    except ImportError as e:
        st.warning(f" Predictive scheduler not available: {str(e)}")
        st.info("Install required packages: `pip install requests numpy`")
    except Exception as e:
        st.error(f" Error in multi-objective optimizer: {str(e)}")
