import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats
from streamlit_autorefresh import st_autorefresh

# --- 1. LIVE HEARTBEAT (Refreshes every 30 seconds) ---
st_autorefresh(interval=30 * 1000, key="datarefresh")

if 'favorites' not in st.session_state:
    st.session_state['favorites'] = ["GC=F", "EURUSD=X", "BTC-USD"]

# --- 2. PROJECTION ENGINE ---
def calculate_projection(df, periods=5):
    """Uses Linear Regression to project the next few candles"""
    y = df['Close'].values
    x = np.arange(len(y))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Predict future points
    future_x = np.arange(len(y), len(y) + periods)
    future_y = slope * future_x + intercept
    
    # Create a future timeframe
    last_date = df.index[-1]
    future_dates = pd.date_range(last_date, periods=periods + 1, freq=df.index.inferred_freq)[1:]
    
    return future_dates, future_y

# --- 3. UI SETUP ---
st.set_page_config(layout="wide", page_title="NexusFlow Live Terminal")
st.title("🏛️ NexusFlow: Live Projections & Real-Time Pulse")

# Sidebar
with st.sidebar:
    st.header("⭐ Watchlist")
    search_query = st.text_input("Find Asset:")
    if st.button("🔍 Add"):
        search = yf.Search(search_query, max_results=1).quotes
        if search:
            st.session_state['favorites'].append(search[0]['symbol'])
            st.rerun()
    
    global_tf = st.selectbox("Timeframe:", ["1m", "5m", "15m", "1h"], index=0)
    st.info(f"Last Live Sync: {pd.Timestamp.now().strftime('%H:%M:%S')}")

# --- 4. MULTI-CHART DISPLAY ---
for asset in st.session_state['favorites']:
    try:
        # Fetching data
        p_map = {"1m": "1d", "5m": "1d", "15m": "5d", "1h": "1mo"}
        df = yf.download(asset, period=p_map[global_tf], interval=global_tf, progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Calculate Projections
        f_dates, f_prices = calculate_projection(df)
        
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            
            with col1:
                curr_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]
                diff = curr_price - prev_price
                st.metric(asset, f"{curr_price:.4f}", f"{diff:.4f}")
                
                # Dynamic Decision
                proj_direction = "UP" if f_prices[-1] > curr_price else "DOWN"
                st.write(f"**Projection:** {proj_direction}")
                st.markdown(f"Status: :{'green' if proj_direction == 'UP' else 'red'}[Analyzing Flow]")

            with col2:
                # MAIN CHART
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], 
                                high=df['High'], low=df['Low'], close=df['Close'], name="Live Data")])
                
                # Add Projection Line (Dashed Orange)
                fig.add_trace(go.Scatter(x=f_dates, y=f_prices, mode='lines+markers', 
                                         line=dict(color='orange', dash='dash'), name="AI Projection"))
                
                fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False,
                                  margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig, use_container_width=True)
    except:
        continue
