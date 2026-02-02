import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.signal import argrelextrema

# --- 1. CORE FUNCTIONS ---

def detect_sr_levels(df, window=10):
    """Detects the most recent 3 support and 3 resistance levels"""
    # Find local maxima (Resistance)
    df['max'] = df.iloc[argrelextrema(df['High'].values, np.greater_equal, order=window)[0]]['High']
    # Find local minima (Support)
    df['min'] = df.iloc[argrelextrema(df['Low'].values, np.less_equal, order=window)[0]]['Low']
    
    # Get the last 3 unique levels to avoid clutter
    res_levels = df['max'].dropna().unique()[-3:].tolist()
    sup_levels = df['min'].dropna().unique()[-3:].tolist()
    
    return sup_levels, res_levels

def get_pro_analysis(symbol, tf):
    p_map = {"1m": "1d", "5m": "5d", "1h": "1mo", "1d": "1y"}
    df = yf.download(symbol, period=p_map[tf], interval=tf, progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    
    # Buy/Sell Power Logic
    bull_power = (df['Close'] - df['Low']).tail(15).sum()
    bear_power = (df['High'] - df['Close']).tail(15).sum()
    buy_pct = (bull_power / (bull_power + bear_power) * 100) if (bull_power + bear_power) > 0 else 50
    
    # Trend Detection
    sma = df['Close'].rolling(20).mean().iloc[-1]
    trend = "UP" if df['Close'].iloc[-1] > sma else "DOWN"
    
    return df, round(buy_pct, 1), trend

# --- 2. DASHBOARD LAYOUT ---
st.set_page_config(layout="wide")
st.title("🏛️ NexusFlow: Institutional Pivot Terminal")

if 'favorites' not in st.session_state:
    st.session_state.favorites = ["GC=F", "EURUSD=X", "BTC-USD"]

# Sidebar Management
with st.sidebar:
    st.header("⭐ Watchlist")
    search = st.text_input("Find Ticker (e.g. Gold, AAPL):")
    if st.button("➕ Add"):
        # Auto-detect logic from previous step
        s = yf.Search(search, max_results=1).quotes
        if s: 
            st.session_state.favorites.append(s[0]['symbol'])
            st.rerun()
    
    st.divider()
    tf = st.selectbox("Timeframe:", ["1m", "5m", "1h", "1d"], index=2)

# --- 3. THE MULTI-CHART GRID ---
for asset in st.session_state.favorites:
    try:
        df, b_pct, trend = get_analysis(asset, tf)
        supports, resistances = detect_sr_levels(df)
        
        with st.container(border=True):
            # Header Row
            c_head1, c_head2, c_head3 = st.columns([1, 2, 1])
            with c_head1:
                st.subheader(asset)
                color = "green" if b_pct > 55 else "red" if b_pct < 45 else "gray"
                st.markdown(f"**Signal:** :{color}[{'BUY' if b_pct > 55 and trend == 'UP' else 'SELL' if b_pct < 45 and trend == 'DOWN' else 'NEUTRAL'}]")
            
            with c_head2:
                # CANDLESTICK CHART
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                
                # Draw Support Lines
                for s in supports:
                    fig.add_hline(y=s, line_dash="dash", line_color="green", opacity=0.5)
                # Draw Resistance Lines
                for r in resistances:
                    fig.add_hline(y=r, line_dash="dash", line_color="red", opacity=0.5)
                    
                fig.update_layout(height=350, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
            with c_head3:
                # LEVELS & PRESSURE
                st.write("📊 **Key Zones**")
                st.caption("Top Resistances:")
                for r in reversed(resistances): st.write(f"🛑 {r:.4f}")
                
                st.caption("Bottom Supports:")
                for s in reversed(supports): st.write(f"✅ {s:.4f}")
                
                st.write(f"Buy Pressure: {b_pct}%")
                st.progress(int(b_pct))
    except Exception as e:
        continue
