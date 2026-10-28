import streamlit as st

st.set_page_config(
    page_title="AI Investment Analyst",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Investment Analyst")

st.write(
    "Enter a stock or ETF ticker to generate a complete investment analysis."
)

ticker = st.text_input(
    "Ticker Symbol",
    placeholder="Example: HOOD, SNOW, AAPL, VOO"
).upper().strip()

analyze = st.button("Analyze Investment", type="primary")

if analyze:
    if ticker:
        st.success(f"Ready to analyze {ticker}")
    else:
        st.warning("Enter a ticker symbol first.")