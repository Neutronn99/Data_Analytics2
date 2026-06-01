import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Nassau Candy Logistics", 
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium light aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
        color: #212529;
    }
    h1, h2, h3 {
        color: #1A1D20;
        font-family: 'Inter', sans-serif;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricValue"] {
        color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Factory-to-Customer Shipping Dashboard")
st.markdown("Analyzing route efficiency, geographic bottlenecks, and shipping performance.")

# --- DATA LOADING & CLEANING CACHE ---
@st.cache_data
def load_data():
    # Load data
    df = pd.read_csv('Nassau Candy Distributor.csv')
    
    # Clean Dates
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, format='mixed')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], dayfirst=True, format='mixed')
    df['Shipping Lead Time'] = (df['Ship Date'] - df['Order Date']).dt.days
    
    # Filter out invalid rows like before to ensure data quality
    df = df[df['Shipping Lead Time'] >= 0]
    df = df.dropna(subset=['Ship Date'])
    
    # Standardize Geography
    df['State/Province'] = df['State/Province'].str.upper()
    df['Region'] = df['Region'].str.title()
    
    # Map Factories
    product_to_factory_map = {
        'Wonka Bar - Triple Dazzle Caramel': "Lot's O' Nuts",
        'Wonka Bar - Nutty Crunch Surprise': "Sugar Shack",
        'Wonka Bar -Scrumdiddlyumptious': "Secret Factory",
        'Wonka Bar - Milk Chocolate': "The Other Factory"
    }
    df['Factory'] = df['Product Name'].map(product_to_factory_map)
    df['Route_to_State'] = df['Factory'] + " -> " + df['State/Province']
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Data")
selected_region = st.sidebar.multiselect(
    "Select Region", 
    options=df['Region'].dropna().unique(), 
    default=df['Region'].dropna().unique()
)
selected_ship_mode = st.sidebar.multiselect(
    "Select Ship Mode", 
    options=df['Ship Mode'].dropna().unique(), 
    default=df['Ship Mode'].dropna().unique()
)

# Apply filters to dataset
filtered_df = df[df['Region'].isin(selected_region) & df['Ship Mode'].isin(selected_ship_mode)]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --- KPI CALCULATIONS ---
route_kpis = filtered_df.groupby('Route_to_State').agg(
    Average_Lead_Time=('Shipping Lead Time', 'mean'),
    Route_Volume=('Order ID', 'count')
).reset_index()

# Format Average Lead Time for display
route_kpis['Average_Lead_Time'] = route_kpis['Average_Lead_Time'].round(2)

# --- DASHBOARD LAYOUT ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 Most Efficient Routes")
    fastest = route_kpis.sort_values(by='Average_Lead_Time').head(10)
    st.dataframe(fastest.style.background_gradient(cmap='Greens', subset=['Average_Lead_Time']), use_container_width=True, hide_index=True)

with col2:
    st.subheader("🚨 Top 10 Geographic Bottlenecks")
    avg_vol = route_kpis['Route_Volume'].mean()
    # Bottlenecks: Higher than average volume, sorted by longest lead time
    bottlenecks = route_kpis[route_kpis['Route_Volume'] > avg_vol].sort_values(by='Average_Lead_Time', ascending=False).head(10)
    st.dataframe(bottlenecks.style.background_gradient(cmap='Reds', subset=['Average_Lead_Time']), use_container_width=True, hide_index=True)

st.divider()

# --- VISUALIZATIONS ---
st.subheader("Ship Mode Performance Comparison")
# Calculate average lead time by ship mode for the bar chart
ship_kpis = filtered_df.groupby('Ship Mode')['Shipping Lead Time'].mean().reset_index()
fig_ship = px.bar(
    ship_kpis, 
    x='Ship Mode', 
    y='Shipping Lead Time', 
    color='Ship Mode', 
    title="Average Lead Time by Ship Mode",
    template="plotly_white",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_ship.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", 
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Shipping Mode",
    yaxis_title="Avg Lead Time (Days)"
)
st.plotly_chart(fig_ship, use_container_width=True)
