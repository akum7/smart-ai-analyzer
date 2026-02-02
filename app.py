import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- 1. CONFIG & SESSION STATE ---
st.set_page_config(page_title="NexusFlow AI Pro", layout="wide")
st.title("🏛️ Institutional AI Terminal")

# Initialize persistent favorites
if 'favorites' not in st.session_state:
    st.session_state.favorites = ["GC=F", "EURUSD=X", "BTC-USD"]

# --- 2. SIDEBAR MANAGER ---
with st.sidebar:
    st.header("⭐ Watchlist Manager")
    # Search and Add
    new_asset = st.text_input("Search Instrument (Ticker):").upper()
    if st.button("➕ Add to Favorites"):
        if new_asset and new_asset not in st.session_state.favorites:
            st.session_state.favorites.append(new_asset)
            st.rerun()
    
    st.divider()
    # Timeframe Global Control
    timeframe = st.selectbox("Global Timeframe:", ["1m", "5m", "1h", "1d"], index=2)
    
    # Favorites list with delete buttons
    st.write("### Monitoring:")
    for fav in st.session_state.favorites:
        col_a, col_b = st.columns([4, 1])
        col_a.write(f"🔍 {fav}")
        if col_b.button("🗑️", key=f"del_{fav}"):
            st.session_state.favorites.remove(fav)
            st.rerun()

# --- 3. THE ANALYSIS ENGINE ---
def get_pro_analysis(symbol, tf):
    # Map timeframe to Yahoo periods
    p_map = {"1m": "1d", "5m": "5d", "1h": "1mo", "1d": "1y"}
    df = yf.download(symbol, period=p_map[tf], interval=tf, progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # Calculate Buy/Sell Pressure (Money Flow Index logic)
    # logic: (Close - Low) vs (High - Close)
    bull_power = (df['Close'] - df['Low']).tail(10).sum()
    bear_power = (df['High'] - df['Close']).tail(10).sum()
    total = bull_power + bear_power
    buy_pct = (bull_power / total * 100) if total > 0 else 50
    
    # Calculate Trend (Moving Average)
    df['SMA20'] = df['Close'].rolling(20).mean()
    last_price = df['Close'].iloc[-1]
    last_sma = df['SMA20'].iloc[-1]
    trend = "UP" if last_price > last_sma else "DOWN"
    
    # Signal Logic
    if buy_pct > 65 and trend == "UP": decision = "🟢 STRONG BUY"
    elif buy_pct < 35 and trend == "DOWN": decision = "🔴 STRONG SELL"
    else: decision = "🟡 NO ACTION"
    
    return df, round(buy_pct, 1), 100 - round(buy_pct, 1), trend, decision

# --- 4. MULTI-INSTRUMENT DISPLAY ---
if st.session_state.favorites:
    # Show instruments in a grid
    for asset in st.session_state.favorites:
        try:
            df, b_pct, s_pct, trend, dec = get_pro_analysis(asset, timeframe)
            
            # Creating a Container for each instrument
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                
                with c1:
                    st.subheader(asset)
                    st.metric("Trend", trend, delta="Bullish" if trend=="UP" else "Bearish")
                    st.write(f"**Decision:** {dec}")
                
                with c2:
                    # Candlestick Chart
                    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], 
                                    high=df['High'], low=df['Low'], close=df['Close'])])
                    fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                
                with c3:
                    st.write("### Pressure Gauge")
                    st.write(f"Buyers: {b_pct}%")
                    st.progress(int(b_pct))
                    st.write(f"Sellers: {s_pct}%")
                    st.progress(int(s_pct))
        except:
            st.error(f"Could not load data for {asset}")
else:
    st.info("Add an instrument in the sidebar to start analysis.")
