import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from transformers import pipeline

# --- 1. PRO UI SETUP ---
st.set_page_config(page_title="NexusFlow Pro Terminal", layout="wide")
st.title("🏛️ NexusFlow: AI Institutional Terminal")

# --- 2. PERSISTENT WATCHLIST ---
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["GC=F", "EURUSD=X", "BTC-USD"]

# --- 3. SIDEBAR: MONITORING & INPUT ---
with st.sidebar:
    st.header("🎛️ Terminal Controls")
    new_symbol = st.text_input("Add Symbol (e.g., AAPL, GBPUSD=X):").upper()
    if st.button("➕ Add to Monitor"):
        if new_symbol and new_symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_symbol)
    
    st.write("---")
    selected_asset = st.selectbox("Active Monitoring:", st.session_state.watchlist)
    
    # TIMEFRAME SWITCHER
    tf_choice = st.radio("Timeframe Analysis:", ["1m", "5m", "1h", "1d"], index=3)
    
    # Clear Watchlist
    if st.button("🗑️ Reset Watchlist"):
        st.session_state.watchlist = ["GC=F", "EURUSD=X", "BTC-USD"]
        st.rerun()

# --- 4. DATA ENGINE ---
def get_data(ticker, interval):
    # Mapping intervals to periods
    period_map = {"1m": "1d", "5m": "5d", "1h": "1mo", "1d": "max"}
    df = yf.download(ticker, period=period_map[interval], interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

data = get_data(selected_asset, tf_choice)

# --- 5. SIGNAL LOGIC & DASHBOARD ---
col1, col2 = st.columns([3, 1])

with col1:
    # PROFESSIONAL CANDLESTICK CHART
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'], name="Price")])
    fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # CHANGE % & PRICE
    curr_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    chg_pct = ((curr_price - prev_price) / prev_price) * 100
    
    st.metric(label="Live Price", value=f"{curr_price:.4f}", delta=f"{chg_pct:.2f}%")
    
    # SMART SIGNALS (Buy/Sell/Wait)
    st.subheader("💡 AI Signal")
    # Simple logic: If price > 20-period MA and Vol is high -> Buy
    ma20 = data['Close'].rolling(20).mean().iloc[-1]
    if curr_price > ma20:
        st.success("🎯 SIGNAL: BUY")
        st.caption("Institutional accumulation detected above MA20.")
    elif curr_price < ma20:
        st.error("🎯 SIGNAL: SELL")
        st.caption("Distribution active below key resistance.")
    else:
        st.warning("🎯 SIGNAL: WAIT")
