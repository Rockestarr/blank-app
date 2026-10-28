import requests
import streamlit as st

API_KEY = st.secrets["FMP_API_KEY"]

tickers = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "TSLA",
    "NFLX",
    "AMD",
    "INTC",
    "AVGO",
    "CRM",
    "ORCL",
    "ADBE",
    "UBER",
    "ABNB",
    "HOOD",
    "SOFI",
    "COIN",
    "PLTR",
    "SNOW",
    "SPOT",
    "JPM",
    "BAC",
    "GS",
    "V",
    "MA",
    "COST",
    "WMT",
    "HD",
    "NKE",
    "MCD",
    "DIS",
    "BA",
    "CAT",
    "XOM",
    "CVX",
    "JNJ",
    "LLY",
    "UNH"
]

BASE_URL = "https://financialmodelingprep.com/stable"

working = []
blocked = []

for ticker in tickers:

    response = requests.get(
        f"{BASE_URL}/income-statement",
        params={
            "symbol": ticker,
            "limit": 1,
            "apikey": API_KEY
        },
        timeout=20
    )

    try:
        data = response.json()
    except Exception:
        data = None

    if (
        response.status_code == 200
        and isinstance(data, list)
        and len(data) > 0
    ):

        working.append(ticker)
        print(f"✅ {ticker}")

    else:

        blocked.append(ticker)
        print(
            f"❌ {ticker} | "
            f"HTTP {response.status_code}"
        )

print()
print("============================")
print("RESULTS")
print("============================")

print()
print(
    f"Full statement access: "
    f"{len(working)}/{len(tickers)}"
)

print()
print("WORKING:")
print(", ".join(working))

print()
print("BLOCKED:")
print(", ".join(blocked))