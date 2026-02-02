import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from scipy.signal import argrelextrema
import numpy as np

# --- 1. SMART ANALYSIS TOOLS ---

def calculate_pressure(df):
    """Calculates Buy vs Sell Pressure Percentage"""
    # CLV (Close Location Value) determines if bulls or bears won the candle
    # If close is near high, bulls are strong. If near low, bears are strong.
    clv = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
    clv = clv.fillna(0)
    
    # Calculate Buying and Selling Volume
    buy_vol = df['Volume'] * (clv.clip(lower=0))
    sell_vol = df['Volume'] * (clv.clip(upper=0).abs())
    
    total_buy = buy_vol.tail(20).sum()
    total_sell = sell_vol.tail(20).sum()
    total = total_buy + total_sell
    
    buy_pct = (total_buy / total * 100) if total > 0 else 50
    sell_pct = (total_sell / total * 100) if total > 0 else 50
    return round(buy_pct, 1), round(sell_pct, 1)

def get_levels(df):
    """Detects major Support and Resistance using local Min/Max"""
    # We look for price points where the trend reversed
    n = 5 # neighborhood to look for peaks
    df['min'] = df.iloc[argrelextrema(df.Close.values, np.less_equal, order=n)[0]]['Close']
    df['max'] = df.iloc[argrelextrema(df.Close.values, np.greater_equal, order=n)[0]]['Close']
    
    supports = df['min'].dropna().unique().tolist()
    resistances = df['max'].dropna().unique().tolist()
    return supports[-3:], resistances[-3:] # Return the last 3 major zones

# --- 2. DASHBOARD UI ---
st.set_page_config(layout="wide")
st.title("🏛️ NexusFlow: Smart Pressure Terminal")

ticker = st.sidebar.text_input("Symbol:", "GC=F")
data = yf.download(ticker, period="6d", interval="1h", progress=False)
if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

# --- 3. THE "REAL-TIME" PRESSURE GAUGE ---
buy_p, sell_p = calculate_pressure(data)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.write("### Buy vs Sell Power")
    st.metric("Bulls (Buy %)", f"{buy_p}%", delta_color="normal")
    st.metric("Bears (Sell %)", f"-{sell_p}%", delta_color="inverse")
    
    # Progress Bar UI
    st.write("Market Balance")
    st.progress(buy_p / 100)

with col2:
    # MAIN CHART WITH S/R LEVELS
    supports, resistances = get_levels(data)
    
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'], name="Price")])
    
    # Add Support Lines (Green)
    for s in supports:
        fig.add_hline(y=s, line_dash="dash", line_color="green", annotation_text="SUPPORT")
        
    # Add Resistance Lines (Red)
    for r in resistances:
        fig.add_hline(y=r, line_dash="dash", line_color="red", annotation_text="RESISTANCE")

    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.write("### Key Zones")
    st.error(f"Resistance: {max(resistances):.2f}" if resistances else "No Resistance Found")
    st.success(f"Support: {min(supports):.2f}" if supports else "No Support Found")
