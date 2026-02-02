import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from transformers import pipeline

# --- 1. SETUP & THEME ---
st.set_page_config(page_title="NexusFlow AI Pro", layout="wide")
st.title("🏛️ NexusFlow: Smart AI Market Intelligence")

# --- 2. GET YOUR FREE API KEY ---
# Go to finnhub.io to get a free key and replace this placeholder
FINNHUB_KEY = st.sidebar.text_input("Enter Finnhub API Key", type="password")

# Sidebar Configuration
asset_map = {
    "Gold (XAUUSD)": "GC=F",
    "EUR/USD": "EURUSD=X",
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^IXIC"
}
asset_label = st.sidebar.selectbox("Market Asset", list(asset_map.keys()))
asset_ticker = asset_map[asset_label]

# --- 3. THE AI "BRAIN" (Sentiment Agent) ---
@st.cache_resource
def load_ai_model():
    # FinBERT understands financial terminology (Hawkish/Dovish)
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

sentiment_ai = load_ai_model()

def fetch_live_news():
    if not FINNHUB_KEY:
        return []
    url = f"https://finnhub.io/api/v1/news?category=forex&token={FINNHUB_KEY}"
    response = requests.get(url)
    return response.json()[:5] if response.status_code == 200 else []

# --- 4. INSTITUTIONAL ORDER BLOCK LOGIC ---
def detect_order_blocks(df):
    # Logic: Look for 2x average volume combined with a large price move
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Price_Change'] = df['Close'].diff().abs()
    # Footprint: High Volume + High Volatility
    df['OB'] = (df['Volume'] > df['Vol_Avg'] * 2.0) & (df['Price_Change'] > df['Price_Change'].mean())
    return df[df['OB'] == True]

# --- 5. DATA PROCESSING ---
data = yf.download(asset_ticker, period="60d", interval="1d")
data.reset_index(inplace=True)
ob_zones = detect_order_blocks(data)

# --- 6. THE SMART DASHBOARD UI ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"📈 {asset_label} Trajectory")
    st.line_chart(data.set_index('Date')['Close'])
    
    st.write("### 🏦 Detected Institutional Zones (Order Blocks)")
    if not ob_zones.empty:
        st.dataframe(ob_zones[['Date', 'Close', 'Volume']].tail(3))
    else:
        st.info("No major institutional footprints detected today.")

with col2:
    st.subheader("🤖 AI Sentiment Barometer")
    news_items = fetch_live_news()
    
    if news_items:
        scores = []
        for item in news_items:
            res = sentiment_ai(item['headline'])[0]
            scores.append(res['label'])
            # Display colored news items
            color = "green" if res['label'] == 'positive' else "red" if res['label'] == 'negative' else "gray"
            st.markdown(f"**{res['label'].upper()}**: {item['headline']}")
        
        # Decision logic
        bulls = scores.count('positive')
        bears = scores.count('negative')
        
        if bulls > bears:
            st.success("🎯 SIGNAL: ACCUMULATION (Bullish)")
        elif bears > bulls:
            st.error("🎯 SIGNAL: DISTRIBUTION (Bearish)")
        else:
            st.warning("🎯 SIGNAL: NO ACTION (Neutral)")
    else:
        st.info("Please enter a Finnhub API Key in the sidebar to see AI News Analysis.")
