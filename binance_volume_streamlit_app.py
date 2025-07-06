import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Binance Volume Spike Scanner", layout="wide")
st.title("📈 Binance USDT Perpetual Volume Spike Scanner")

@st.cache_data(ttl=300)
def get_usdt_perpetual_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    res = requests.get(url).json()
    return [
        s['symbol'] for s in res['symbols']
        if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT'
    ]

def get_klines(symbol, interval='15m', limit=500):
    url = f"https://fapi.binance.com/fapi/v1/klines"
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    res = requests.get(url, params=params).json()
    df = pd.DataFrame(res, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'])
    df['quote_volume'] = df['quote_volume'].astype(float)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    return df

def scan_volume_spikes():
    matches = []
    symbols = get_usdt_perpetual_symbols()
    for symbol in symbols:
        try:
            df = get_klines(symbol)
            current_vol = df.iloc[-1]['quote_volume']
            avg_vol = df.iloc[:-1]['quote_volume'].mean()
            if current_vol >= 100_000_000 and current_vol >= 10 * avg_vol:
                matches.append({
                    'Symbol': symbol,
                    'Time': df.iloc[-1]['open_time'],
                    'Current Quote Volume ($)': round(current_vol, 2),
                    'Avg Quote Volume ($)': round(avg_vol, 2)
                })
        except:
            pass
    return pd.DataFrame(matches)

if st.button("🔁 Refresh Now"):
    with st.spinner("Scanning Binance Futures..."):
        result_df = scan_volume_spikes()
        if not result_df.empty:
            st.success(f"Found {len(result_df)} spike(s)!")
            st.dataframe(result_df.sort_values(by="Current Quote Volume ($)", ascending=False))
        else:
            st.info("✅ No volume spikes detected.")
else:
    st.caption("Click the button above to manually refresh. This data auto-updates every 5 minutes.")
