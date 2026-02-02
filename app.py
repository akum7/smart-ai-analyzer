import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from transformers import pipeline

# --- 1. SETUP ---
st.set_page_config(page_title="NexusFlow AI Pro", layout="wide")
st.title("🏛️ NexusFlow: Smart AI Market Intelligence")

# Access the Secret Key safely
try:
    FINNHUB_KEY = st.secrets["FINNHUB_API_KEY"]
except:
    st.sidebar.warning("⚠️ Finnhub API Key not found in Streamlit Secrets.")
    FINNHUB_KEY = None

# Sidebar Config
asset_map = {
    "Gold (XAUUSD)": "GC=F",
    "EUR/USD": "EURUSD=X",
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^IXIC"
}
asset_label = st.sidebar.selectbox("Market Asset", list(asset_map.keys()))
asset_ticker = asset_map[asset_label]

# --- 2. THE AI BRAIN ---
@st.cache_resource
def load_ai_model():
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

sentiment_ai = load_ai_model()

def fetch_live_news():
    if not FINNHUB_KEY: return []
    url = f"https://finnhub.io/api/v1/news?category=forex&token={FINNHUB_KEY}"
    response = requests.get(url)
    return response.json()[:5] if response.status_code == 200 else []

# --- 3. THE "SMART" DATA FIX & ORDER BLOCKS ---
def get_clean_data(ticker):
    # Download data
    df = yf.download(ticker, period="60d", interval="1d")
    
    # FIX: Flatten Multi-Index columns if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.reset_index(inplace=True)
    return df

def detect_order_blocks(df):
    df = df.copy()
    # Math logic for Institutional footprints
    df['Vol_Avg'] = df['Volume'].rolling(20).mean()
    df['Price_Change'] = df['Close'].diff().abs()
    
    # Logic: High Volume (2x avg) + Price Momentum
    condition = (df['Volume'] > df['Vol_Avg'] * 2.0) & (df['Price_Change'] > df['Price_Change'].mean())
    df['OB'] = condition
    return df[df['OB'] == True]

# Execute Data Processing
data = get_clean_data(asset_ticker)
ob_zones = detect_order_blocks(data)

# --- 4. THE DASHBOARD UI ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"📈 {asset_label} Trajectory")
    # Show the main price chart
    st.line_chart(data.set_index('Date')['Close'])
    
    st.write("### 🏦 Institutional Order Blocks")
    if not ob_zones.empty:
        st.dataframe(ob_zones[['Date', 'Close', 'Volume']].tail(3))
    else:
        st.info("Searching for big institutional entries...")

with col2:
    st.subheader("🤖 AI Sentiment Barometer")
    news_items = fetch_live_news()
    
    if news_items:
        scores = []
        for item in news_items:
            res = sentiment_ai(item['headline'])[0]
            scores.append(res['label'])
            color = "green" if res['label'] == 'positive' else "red" if res['label'] == 'negative' else "gray"
            st.markdown(f"**{res['label'].upper()}**: {item['headline']}")
        
        # Decision Logic
        bulls, bears = scores.count('positive'), scores.count('negative')
        if bulls > bears: st.success("🎯 SIGNAL: ACCUMULATION (Bullish)")
        elif bears > bulls: st.error("🎯 SIGNAL: DISTRIBUTION (Bearish)")
        else: st.warning("🎯 SIGNAL: NO ACTION (Neutral)")
    else:
        st.info("Waiting for Finnhub news feed...")
