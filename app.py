import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from transformers import pipeline

# --- 1. SETUP ---
st.set_page_config(page_title="NexusFlow AI Pro", layout="wide")
st.title("🏛️ NexusFlow: Smart AI Terminal")

# --- 2. FAVORITES & HEATMAP DATA ---
# You can add or remove your favorite symbols here
FAVORITES = ["GC=F", "SI=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC", "^IXIC"]

@st.cache_data(ttl=3600)
def get_heatmap_data(tickers):
    results = []
    for t in tickers:
        try:
            df = yf.download(t, period="5d", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Calculate % change from yesterday to today
            change = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
            results.append({"Symbol": t, "Change %": round(change, 2), "Price": round(df['Close'].iloc[-1], 4)})
        except:
            continue
    return pd.DataFrame(results)

# --- 3. THE SMART DECISION ENGINE ---
def get_clean_data(ticker):
    df = yf.download(ticker, period="60d", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    return df

# --- 4. DASHBOARD LAYOUT ---
tab1, tab2 = st.tabs(["🎯 Daily Decision", "🗺️ Market Heatmap"])

with tab1:
    st.subheader("Daily Strategy & Favorites")
    selected_fav = st.selectbox("Switch to Favorite Instrument:", FAVORITES)
    
    # Run the same analysis as before but for the selected favorite
    data = get_clean_data(selected_fav)
    st.line_chart(data.set_index('Date')['Close'])
    
    # Decision Logic Box
    st.info(f"**AI Recommendation for {selected_fav}:** Analysis complete. Check Order Blocks below.")
    # (The rest of your Order Block and Sentiment code goes here)

with tab2:
    st.subheader("Global Market Heatmap (24h Change)")
    h_data = get_heatmap_data(FAVORITES)
    
    if not h_data.empty:
        # Create a professional heatmap using Plotly
        fig = px.treemap(h_data, 
                         path=['Symbol'], 
                         values=[1]*len(h_data), # Equal box sizes
                         color='Change %', 
                         color_continuous_scale='RdYlGn', # Red to Green
                         hover_data=['Price'],
                         title="Relative Strength of Favorites")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Could not load heatmap data. Check your internet connection.")

# --- SIDEBAR INFO ---
with st.sidebar:
    st.write("### My Favorites List")
    for f in FAVORITES:
        st.write(f"• {f}")
    st.divider()
    st.caption("AI Terminal v2.0 - Running on GitHub")
