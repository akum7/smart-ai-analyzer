import streamlit as st
import yfinance as yf

# --- NEW SEARCH LOGIC ---
def deep_ticker_search(query):
    """Try multiple formats to find the correct Yahoo Ticker"""
    if not query: return None, None
    
    # 1. Direct Search using Yahoo's internal lookup
    try:
        search = yf.Search(query, max_results=1)
        if search.quotes:
            return search.quotes[0]['symbol'], search.quotes[0].get('shortname', query)
    except:
        pass

    # 2. Common Forex/Metal Fixes (if search fails)
    replacements = {
        "XAUUSD": "GC=F",
        "XAGUSD": "SI=F",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "GOLD": "GC=F"
    }
    
    clean_query = query.replace("/", "").replace("-", "").upper()
    if clean_query in replacements:
        ticker = replacements[clean_query]
        return ticker, query
        
    return None, None

# --- UPDATED SIDEBAR ---
with st.sidebar:
    st.header("⭐ Watchlist Manager")
    user_input = st.text_input("Enter Asset (e.g., Gold, Apple, XAUUSD):")
    
    if st.button("🔍 Find & Add"):
        ticker, name = deep_ticker_search(user_input)
        if ticker:
            if ticker not in st.session_state.favorites:
                st.session_state.favorites.append(ticker)
                st.success(f"Found: {name} ({ticker})")
                st.rerun()
            else:
                st.info(f"{ticker} is already in your list.")
        else:
            st.error("Could not find a matching ticker. Try being more specific (e.g., 'Gold Futures').")
