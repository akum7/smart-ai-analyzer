import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats
from streamlit_autorefresh import st_autorefresh

# --- 1. INITIALIZATION ---
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = ["GC=F", "BTC-USD", "EURUSD=X"]

# 30-second live refresh heartbeat
st_autorefresh(interval=30 * 1000, key="datarefresh")

# --- 2. THE PRESSURE & PROJECTION ENGINE ---
def get_market_analysis(symbol, tf):
    """Fetches data with STRICT period limits to prevent 'Month Data' bug"""
    # Yahoo Limit Handler
    if tf == "1m":
        req_period = "7d"   # Max for 1m
    elif tf in ["5m", "15m"]:
        req_period = "60d"  # Max for intraday < 1h
    elif tf == "1h":
        req_period = "2y"   # 1h data is usually available for 2 years
    else:
        req_period = "max"

    try:
        # Download data
        df = yf.download(symbol, period=req_period, interval=tf, progress=False)
        
        if df.empty or len(df) < 10: 
            return None
            
        # Fix MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        # 🟢 BUY VS 🔴 SELL PRESSURE (Anatomy of the last 14 candles)
        # Calculates 'Bullish' vs 'Bearish' wick and body strength
        bull_strength = (df['Close'] - df['Low']).tail(14).sum()
        bear_strength = (df['High'] - df['Close']).tail(14).sum()
        total_p = bull_strength + bear_strength
        
        buy_pct = round((bull_strength / total_p * 100), 1) if total_p > 0 else 50
        sell_pct = 100 - buy_pct

        # PROJECTION ENGINE (Linear Regression for next 5 bars)
        y = df['Close'].values
        x = np.arange(len(y))
        slope, intercept, _, _, _ = stats.linregress(x, y)
        
        future_x = np.arange(len(y), len(y) + 5)
        future_y = slope * future_x + intercept
        
        # Create timestamps for projection
        last_time = df.index[-1]
        freq_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}
        f_dates = pd.date_range(last_time, periods=6, freq=freq_map.get(tf, "1D"))[1:]

        return {
            "df": df,
            "buy_p": buy_pct,
            "sell_p": sell_pct,
            "f_dates": f_dates,
            "f_prices": future_y,
            "curr": df['Close'].iloc[-1],
            "prev": df['Close'].iloc[-2]
        }
    except Exception as e:
        return None

# --- 3. UI LAYOUT ---
st.set_page_config(layout="wide", page_title="NexusFlow Terminal")
st.title("🏛️ NexusFlow Institutional Terminal")

with st.sidebar:
    st.header("🎛️ Watchlist")
    
    # ADD ASSET
    new_asset = st.text_input("Find Ticker (e.g. Gold, AAPL, BTC):")
    if st.button("➕ Add to Feed"):
        search = yf.Search(new_asset, max_results=1).quotes
        if search:
            ticker = search[0]['symbol']
            if ticker not in st.session_state['favorites']:
                st.session_state['favorites'].append(ticker)
                st.rerun()
    
    st.divider()
    global_tf = st.selectbox("Interval:", ["1m", "5m", "15m", "1h"], index=0)
    
    # MANAGE LIST
    st.write("### Active Monitors")
    for fav in st.session_state['favorites']:
        c1, c2 = st.columns([4, 1])
        c1.write(f"📊 {fav}")
        if c2.button("🗑️", key=f"del_{fav}"):
            st.session_state['favorites'].remove(fav)
            st.rerun()

# --- 4. MAIN DASHBOARD DISPLAY ---
st.caption(f"Next Pulse Update in 30s | Current Time: {pd.Timestamp.now().strftime('%H:%M:%S')}")

for asset in st.session_state['favorites']:
    data = get_market_analysis(asset, global_tf)
    
    if data:
        with st.container(border=True):
            col_metrics, col_chart = st.columns([1, 4])
            
            with col_metrics:
                st.subheader(asset)
                change = data['curr'] - data['prev']
                st.metric("Live Price", f"{data['curr']:.4f}", f"{change:.4f}")
                
                # PRESSURE GAUGES
                st.write("**Pressure Pulse**")
                st.caption(f"🟢 Buy: {data['buy_p']}%")
                st.progress(data['buy_p'] / 100)
                st.caption(f"🔴 Sell: {data['sell_p']}%")
                st.progress(data['sell_p'] / 100)
                
                # AI RECOMMENDATION
                if data['buy_p'] > 60:
                    st.success("🎯 STRONG BUY")
                elif data['sell_p'] > 60:
                    st.error("📉 STRONG SELL")
                else:
                    st.warning("⚖️ NEUTRAL")

            with col_chart:
                # CANDLESTICK + PROJECTION
                fig = go.Figure()
                
                # Actual Market Data
                fig.add_trace(go.Candlestick(
                    x=data['df'].index, open=data['df']['Open'],
                    high=data['df']['High'], low=data['df']['Low'],
                    close=data['df']['Close'], name="Market"
                ))
                
                # AI Projection Line
                fig.add_trace(go.Scatter(
                    x=data['f_dates'], y=data['f_prices'],
                    mode='lines+markers', line=dict(color='orange', width=3, dash='dash'),
                    name="AI Path"
                ))
                
                fig.update_layout(
                    height=350, template="plotly_dark", 
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=0, r=0, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Waiting for {asset} data... (Yahoo limit likely hit for this interval)")
