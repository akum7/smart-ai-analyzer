import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats
from streamlit_autorefresh import st_autorefresh

# --- 1. INITIALIZATION & LIVE SYNC ---
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = ["GC=F", "BTC-USD", "EURUSD=X"]

# Auto-refresh every 30 seconds to keep the "Live" feel
st_autorefresh(interval=30 * 1000, key="datarefresh")

# --- 2. THE PRESSURE & PROJECTION ENGINE ---
def get_market_analysis(symbol, tf):
    p_map = {"1m": "1d", "5m": "1d", "15m": "5d", "1h": "1mo"}
    df = yf.download(symbol, period=p_map[tf], interval=tf, progress=False)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

    # 🟢 BUY VS 🔴 SELL PRESSURE LOGIC
    # We calculate the distance of the Close from the Low (Bulls) and High (Bears)
    bull_vol = (df['Close'] - df['Low']).tail(14).sum()
    bear_vol = (df['High'] - df['Close']).tail(14).sum()
    total = bull_vol + bear_vol
    buy_pct = round((bull_vol / total * 100), 1) if total > 0 else 50
    sell_pct = 100 - buy_pct

    # PROJECTION LOGIC (Linear Regression)
    y = df['Close'].values
    x = np.arange(len(y))
    slope, intercept, _, _, _ = stats.linregress(x, y)
    future_x = np.arange(len(y), len(y) + 5)
    future_y = slope * future_x + intercept
    future_dates = pd.date_range(df.index[-1], periods=6, freq=df.index.inferred_freq)[1:]

    return {
        "df": df,
        "buy_p": buy_pct,
        "sell_p": sell_pct,
        "f_dates": future_dates,
        "f_prices": future_y,
        "curr": df['Close'].iloc[-1]
    }

# --- 3. UI LAYOUT ---
st.set_page_config(layout="wide", page_title="NexusFlow AI")
st.title("🏛️ NexusFlow: Live Institutional Terminal")

with st.sidebar:
    st.header("🎛️ Watchlist Control")
    # Search and Add
    new_asset = st.text_input("Search (e.g. Gold, AAPL, BTC):")
    if st.button("➕ Add Asset"):
        search = yf.Search(new_asset, max_results=1).quotes
        if search and search[0]['symbol'] not in st.session_state['favorites']:
            st.session_state['favorites'].append(search[0]['symbol'])
            st.rerun()
    
    st.divider()
    global_tf = st.selectbox("Global Timeframe:", ["1m", "5m", "15m", "1h"], index=0)
    
    # Delete Section
    st.write("### Active Instruments")
    for fav in st.session_state['favorites']:
        c1, c2 = st.columns([4, 1])
        c1.write(f"🔍 {fav}")
        if c2.button("🗑️", key=f"del_{fav}"):
            st.session_state['favorites'].remove(fav)
            st.rerun()

# --- 4. MAIN DASHBOARD ---
for asset in st.session_state['favorites']:
    data = get_market_analysis(asset, global_tf)
    if data:
        with st.container(border=True):
            # Header Row with Pressure Metrics
            col_info, col_chart = st.columns([1, 3])
            
            with col_info:
                st.subheader(asset)
                st.metric("Price", f"{data['curr']:.4f}")
                
                # Pressure Display
                st.write("**Market Pressure**")
                st.write(f"🟢 Buyers: {data['buy_p']}%")
                st.progress(data['buy_p'] / 100)
                st.write(f"🔴 Sellers: {data['sell_p']}%")
                st.progress(data['sell_p'] / 100)
                
                # Trend Decision
                decision = "STRONG BUY" if data['buy_p'] > 60 else "STRONG SELL" if data['sell_p'] > 60 else "NEUTRAL"
                st.info(f"AI Decision: {decision}")

            with col_chart:
                fig = go.Figure(data=[go.Candlestick(
                    x=data['df'].index, open=data['df']['Open'],
                    high=data['df']['High'], low=data['df']['Low'],
                    close=data['df']['Close'], name="Market"
                )])
                
                # Add Projection
                fig.add_trace(go.Scatter(
                    x=data['f_dates'], y=data['f_prices'],
                    mode='lines+markers', line=dict(color='orange', dash='dash'),
                    name="AI Projection"
                ))
                
                fig.update_layout(height=400, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig, use_container_width=True)
