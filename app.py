import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.signal import argrelextrema

# --- 1. INITIALIZATION (Must be FIRST to prevent AttributeError) ---
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = ["GC=F", "EURUSD=X", "BTC-USD"]

# --- 2. SMART SEARCH & ANALYSIS FUNCTIONS ---

def find_ticker(query):
    """Deep search for tickers like Gold, Silver, or Apple"""
    try:
        search = yf.Search(query, max_results=1).quotes
        if search:
            return search[0]['symbol'], search[0].get('shortname', query)
    except:
        pass
    return None, None

def get_market_data(symbol, interval):
    """Fetch data and calculate Pressure + S/R Levels"""
    p_map = {"1m": "1d", "5m": "5d", "1h": "1mo", "1d": "1y"}
    df = yf.download(symbol, period=p_map[interval], interval=interval, progress=False)
    if df.empty: return None, None, None, None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # Calculate Buy vs Sell Pressure %
    # logic: Distance from Low to Close (Buy) vs High to Close (Sell)
    bull = (df['Close'] - df['Low']).tail(10).sum()
    bear = (df['High'] - df['Close']).tail(10).sum()
    buy_pct = round((bull / (bull + bear) * 100), 1) if (bull + bear) > 0 else 50
    
    # Detect S/R Levels (last 2 significant peaks)
    df['min'] = df.iloc[argrelextrema(df.Low.values, np.less_equal, order=5)[0]]['Low']
    df['max'] = df.iloc[argrelextrema(df.High.values, np.greater_equal, order=5)[0]]['High']
    supports = df['min'].dropna().unique()[-2:].tolist()
    resistances = df['max'].dropna().unique()[-2:].tolist()
    
    return df, buy_pct, supports, resistances

# --- 3. THE USER INTERFACE ---
st.set_page_config(layout="wide", page_title="NexusFlow Terminal")
st.title("🏛️ Institutional AI Analysis Terminal")

# SIDEBAR: Search & Global Settings
with st.sidebar:
    st.header("⭐ Watchlist Manager")
    search_input = st.text_input("Find Instrument (e.g. Gold, BTC):")
    if st.button("🔍 Add to Favorites"):
        tick, name = find_ticker(search_input)
        if tick and tick not in st.session_state['favorites']:
            st.session_state['favorites'].append(tick)
            st.rerun()

    st.divider()
    global_tf = st.selectbox("Global Timeframe:", ["1m", "5m", "1h", "1d"], index=2)
    
    st.write("### Current List")
    for fav in st.session_state['favorites']:
        c_a, c_b = st.columns([4, 1])
        c_a.write(fav)
        if c_b.button("🗑️", key=f"del_{fav}"):
            st.session_state['favorites'].remove(fav)
            st.rerun()

# --- 4. MULTI-CHART DASHBOARD GRID ---
for asset in st.session_state['favorites']:
    df, buy_p, sup, res = get_market_data(asset, global_tf)
    if df is not None:
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                st.subheader(f"{asset}")
                trend = "UP" if df['Close'].iloc[-1] > df['Close'].rolling(20).mean().iloc[-1] else "DOWN"
                st.write(f"Trend: **{trend}**")
                
                # Decision Logic
                if buy_p > 60 and trend == "UP":
                    st.success("🟢 STRONG BUY")
                elif buy_p < 40 and trend == "DOWN":
                    st.error("🔴 STRONG SELL")
                else:
                    st.warning("🟡 AVOID / FLAT")

            with col2:
                # CANDLESTICK CHART
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                for s in sup: fig.add_hline(y=s, line_color="green", line_dash="dash")
                for r in res: fig.add_hline(y=r, line_color="red", line_dash="dash")
                fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            with col3:
                st.write("**Pressure Analysis**")
                st.write(f"Bulls: {buy_p}%")
                st.progress(int(buy_p))
                st.write(f"Bears: {100-buy_p}%")
                st.progress(int(100-buy_p))
                
                st.write("**Levels**")
                st.caption(f"Last Res: {res[-1]:.4f}" if res else "N/A")
                st.caption(f"Last Sup: {sup[-1]:.4f}" if sup else "N/A")
