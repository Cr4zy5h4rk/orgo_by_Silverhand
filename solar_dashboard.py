import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import glob
from datetime import datetime
import folium
from streamlit_folium import folium_static
import numpy as np

# Page configuration
st.set_page_config(
    page_title="🌞 GreenRay - Solar Analysis",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern interface
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 50%, #FFD23F 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FF6B35;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: linear-gradient(90deg, #00C851 0%, #007E33 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(90deg, #ffbb33 0%, #ff8800 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: linear-gradient(90deg, #ff4444 0%, #cc0000 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .location-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class SolarDashboard:
    def __init__(self, results_folder="solar_reports"):
        self.results_folder = results_folder
        
    def load_results(self):
        """Load all available results"""
        files = glob.glob(f"{self.results_folder}/solar_calc_*.json")
        if not files:
            return []
        
        results = []
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
        
        return sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def create_map(self, lat, lon, address):
        """Create an interactive map"""
        if lat and lon:
            m = folium.Map(location=[lat, lon], zoom_start=12)
            
            folium.Marker(
                [lat, lon],
                popup=f"🏠 {address}",
                tooltip="Click for more info",
                icon=folium.Icon(color='orange', icon='sun', prefix='fa')
            ).add_to(m)
            
            return m
        return None
    
    def create_production_gauge(self, production, max_production=8000):
        """Create a production gauge"""
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = production or 0,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Annual Production (kWh)"},
            delta = {'reference': max_production * 0.5},
            gauge = {
                'axis': {'range': [None, max_production]},
                'bar': {'color': "#FF6B35"},
                'steps': [
                    {'range': [0, max_production * 0.3], 'color': "#ffcccc"},
                    {'range': [max_production * 0.3, max_production * 0.7], 'color': "#ffaa99"},
                    {'range': [max_production * 0.7, max_production], 'color': "#ff8866"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_production * 0.8
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            font={'color': "#333333", 'family': "Arial"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        return fig
    
    def create_savings_chart(self, production, electricity_cost):
        """Create a 25-year savings chart"""
        if not production or not electricity_cost:
            return None
        
        years = list(range(1, 26))
        annual_savings = production * electricity_cost
        cumulative_savings = [annual_savings * year for year in years]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=years,
            y=cumulative_savings,
            mode='lines+markers',
            name='Cumulative Savings',
            line=dict(color='#FF6B35', width=3),
            marker=dict(size=6, color='#FF6B35'),
            fill='tonexty',
            fillcolor='rgba(255, 107, 53, 0.1)'
        ))
        
        system_cost = 15000
        fig.add_hline(y=system_cost, line_dash="dash", line_color="red", 
                     annotation_text="System Cost", annotation_position="bottom right")
        
        fig.update_layout(
            title="💰 Cumulative Savings Over 25 Years",
            xaxis_title="Years",
            yaxis_title="Savings ($)",
            template="plotly_white",
            height=400,
            showlegend=True
        )
        
        return fig
    
    def display_metrics(self, data):
        """Display main metrics"""
        extracted = data.get('extracted_data', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            production = extracted.get('annual_production_kwh')
            if production:
                st.metric(
                    label="🔋 Annual Production",
                    value=f"{production:,.0f} kWh",
                    delta=f"For 5kWp installed"
                )
            else:
                st.metric(label="🔋 Annual Production", value="Not available")
        
        with col2:
            irradiation = extracted.get('irradiation_kwh_m2')
            if irradiation:
                st.metric(
                    label="☀️ Solar Irradiation",
                    value=f"{irradiation:,.0f} kWh/m²",
                    delta="Per year"
                )
            else:
                st.metric(label="☀️ Solar Irradiation", value="Not available")
        
        with col3:
            cost = extracted.get('electricity_cost_usd_kwh')
            if cost:
                st.metric(
                    label="💡 Electricity Cost",
                    value=f"${cost:.3f}/kWh",
                    delta=f"Country: {extracted.get('country', 'N/A')}"
                )
            else:
                st.metric(label="💡 Electricity Cost", value="Not available")
        
        with col4:
            if production and cost:
                savings = production * cost
                st.metric(
                    label="💰 Annual Savings",
                    value=f"${savings:,.0f}",
                    delta="Estimate"
                )
            else:
                st.metric(label="💰 Annual Savings", value="Not calculable")
    
    def run(self):
        """Launch main interface"""
        st.markdown("""
        <div class="main-header">
            <h1>🌞 GreenRay Dashboard</h1>
            <p>Intelligent Solar Potential Analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        results = self.load_results()
        
        if not results:
            st.error("❌ No results found. Please run a solar analysis first.")
            st.info("💡 To generate data, use the SolarCalcOrgo class to analyze addresses.")
            return
        
        with st.sidebar:
            st.header("⚙️ Settings")
            
            addresses = [f"{r.get('address', 'Unknown address')} ({r.get('timestamp', 'N/A')})" 
                        for r in results]
            
            selected_idx = st.selectbox(
                "Select an analysis:",
                range(len(addresses)),
                format_func=lambda x: addresses[x]
            )
            
            if st.button("🔄 Refresh data"):
                st.rerun()
        
        selected_data = results[selected_idx]
        
        st.subheader("📊 Key Metrics")
        self.display_metrics(selected_data)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🔍 Analysis")
            extracted = selected_data.get('extracted_data', {})
            status = extracted.get('status', 'unknown')
            
            if status == 'completed':
                st.markdown('<div class="success-box">✅ <strong>Complete analysis</strong></div>', unsafe_allow_html=True)
            elif status == 'partial':
                st.markdown('<div class="warning-box">⚠️ <strong>Partial analysis</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box">❌ <strong>Analysis failed</strong></div>', unsafe_allow_html=True)
            
            lat = extracted.get('latitude')
            lon = extracted.get('longitude')
            
            if lat and lon:
                st.markdown(f"""
                <div class="location-info">
                    <h3>📍 Location</h3>
                    <p><strong>Coordinates:</strong> {lat:.4f}°, {lon:.4f}°</p>
                    <p><strong>Country:</strong> {extracted.get('country', 'Not identified')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            production = extracted.get('annual_production_kwh')
            if production:
                st.subheader("⚡ Production Gauge")
                gauge_fig = self.create_production_gauge(production)
                st.plotly_chart(gauge_fig, use_container_width=True)
        
        if extracted.get('latitude') and extracted.get('longitude'):
            st.subheader("🗺️ Location Map")
            map_obj = self.create_map(
                extracted['latitude'], 
                extracted['longitude'], 
                selected_data.get('address', 'Location')
            )
            if map_obj:
                folium_static(map_obj, width=700, height=400)
        
        production = extracted.get('annual_production_kwh')
        cost = extracted.get('electricity_cost_usd_kwh')
        
        if production and cost:
            st.subheader("📈 Economic Analysis")
            savings_fig = self.create_savings_chart(production, cost)
            st.plotly_chart(savings_fig, use_container_width=True)

def main():
    dashboard = SolarDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()