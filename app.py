import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy import stats
from streamlit_autorefresh import st_autorefresh

# --- 1. INITIALIZATION & REFRESH ---
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = ["GC=F", "BTC-USD", "EURUSD=X"]

# Forces the app to check for new data every 30 seconds
st_autorefresh(interval=30 * 1000, key="pulse_sync")

# --- 2. THE ENGINE (Fixed for Intraday) ---
def get_clean_analysis(symbol, tf):
    # Mapping strict periods to avoid the "Monthly Data" bug
    p_map = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "1mo"}
    req_period = p_map.get(tf, "1mo")

    try:
        df = yf.download(symbol, period=req_period, interval=tf, progress=False)
        
        if df.empty or len(df) < 5: 
            return None
            
        # Standardize columns
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)

        # PRESSURE CALCULATION
        # Distance of close from high/low in the last 10 candles
        bull = (df['Close'] - df['Low']).tail(10).sum()
        bear = (df['High'] - df['Close']).tail(10).sum()
        total = bull + bear
        buy_p = round((bull / total * 100), 1) if total > 0 else 50
        
        # PROJECTION
        y = df['Close'].values
        x = np.arange(len(y))
        slope, intercept, _, _, _ = stats.linregress(x, y)
        f_x = np.arange(len(y), len(y) + 5)
        f_y = slope * f_x + intercept
        
        # Time alignment for projection
        freq_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}
        f_dates = pd.date_range(df.index[-1], periods=6, freq=freq_map.get(tf, "1min"))[1:]

        return {
            "df": df, "buy_p": buy_p, "sell_p": 100 - buy_p,
            "f_dates": f_dates, "f_prices": f_y, "curr": df['Close'].iloc[-1]
        }
    except:
        return None

# --- 3. THE UI ---
st.set_page_config(layout="wide", page_title="NexusFlow Terminal")
st.title("🏛️ NexusFlow: Real-Time Terminal")

with st.sidebar:
    st.header("🎛️ Settings")
    new_asset = st.text_input("Add Ticker (e.g. Gold, BTC):")
    if st.button("➕ Add"):
        search = yf.Search(new_asset, max_results=1).quotes
        if search:
            st.session_state['favorites'].append(search[0]['symbol'])
            st.rerun()

    st.divider()
    # When this changes, it triggers the 'key' below to reset charts
    global_tf = st.selectbox("Interval:", ["1m", "5m", "15m", "1h"], index=0)
    
    st.write("### Watchlist")
    for fav in st.session_state['favorites']:
        c1, c2 = st.columns([4, 1])
        c1.write(fav)
        if c2.button("🗑️", key=f"del_{fav}"):
            st.session_state['favorites'].remove(fav)
            st.rerun()

# --- 4. THE LIVE FEED ---
st.caption(f"Sync: {pd.Timestamp.now().strftime('%H:%M:%S')} | Interval: {global_tf}")

for asset in st.session_state['favorites']:
    data = get_clean_analysis(asset, global_tf)
    
    if data:
        with st.container(border=True):
            col_m, col_c = st.columns([1, 3])
            
            with col_m:
                st.subheader(asset)
                st.metric("Price", f"{data['curr']:.4f}")
                st.write(f"🟢 Buy: {data['buy_p']}%")
                st.progress(data['buy_p'] / 100)
                st.write(f"🔴 Sell: {data['sell_p']}%")
                st.progress(data['sell_p'] / 100)
                
            with col_c:
                # IMPORTANT: THE KEY=f"{asset}_{global_tf}" FORCES THE CHART TO RESET ITS ZOOM
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data['df'].index, open=data['df']['Open'],
                    high=data['df']['High'], low=data['df']['Low'],
                    close=data['df']['Close'], name="Market"
                ))
                fig.add_trace(go.Scatter(
                    x=data['f_dates'], y=data['f_prices'],
                    mode='lines+markers', line=dict(color='orange', dash='dash'), name="AI Prediction"
                ))
                
                # Limit the view to the most recent data only
                # This prevents the chart from showing months of empty space
                fig.update_xaxes(range=[data['df'].index[-40], data['f_dates'][-1]])
                
                fig.update_layout(height=350, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{asset}_{global_tf}")
