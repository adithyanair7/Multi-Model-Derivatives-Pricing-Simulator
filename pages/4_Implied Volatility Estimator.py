import streamlit as st
import yfinance as yf
import math
from scipy.stats import norm
from scipy.optimize import brentq
import plotly.graph_objects as go

# ---- Black-Scholes Function ----
def black_scholes_price(S, K, T, r, sigma, option_type='call'):
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if option_type == 'call':
        return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    else:
        return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# ---- Brent's Method for IV ----
def implied_volatility(S, K, T, r, market_price, option_type='call'):
    def objective(sigma):
        return black_scholes_price(S, K, T, r, sigma, option_type) - market_price

    try:
        return brentq(objective, 1e-6, 5.0)
    except ValueError:
        return None

# ---- Page Setup ----
st.set_page_config(page_title="Implied Volatility", layout="centered")
st.title("Implied Volatility Estimator")
st.markdown(
    """
    <div style='
        display: inline-block;
        padding: 0.35rem 0.75rem;
        background-color: #333333;
        border-radius: 6px;
        border: 2px solid black;
        font-size: 14.5px;
        color: #ffffff;
        font-family: Georgia, serif;
        margin-bottom: 1rem;
        max-width: fit-content;
    '>
        Estimates market-implied volatility using Brent’s method.
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Sidebar Inputs ----
with st.sidebar:
    ticker = st.text_input("Stock Ticker")
    market_price = st.number_input("Market Option Price ($)", min_value=0.01, format="%.2f")
    strike = st.number_input("Strike Price ($)", min_value=0.0, format="%.2f")
    T_days = st.number_input("Time to Maturity (Days)", min_value=1)
    r_percent = st.number_input("Risk-Free Rate (%)", min_value=0.0, format="%.2f")

    option_label_map = {"Call": "call", "Put": "put"}
    option_display = st.selectbox("Option Type", list(option_label_map.keys()))
    option_type = option_label_map[option_display]

    chart_range_display = st.selectbox(
        "Chart Range",
        options=["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "Max"],
        index=3
    )

# ---- Convert Inputs ----
T = T_days / 365
r = r_percent / 100

# ---- Chart Mappings ----
display_to_yf = {
    "1D": "1d", "5D": "5d", "1M": "1mo", "6M": "6mo",
    "YTD": "ytd", "1Y": "1y", "5Y": "5y", "Max": "max"
}
range_to_interval = {
    "1d": "5m", "5d": "15m", "1mo": "1h", "6mo": "1d",
    "ytd": "1d", "1y": "1d", "5y": "1wk", "max": "1mo"
}

# ---- Main Logic ----
if ticker:
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get("regularMarketPrice")
        if price is None:
            raise ValueError("Stock not found. Please check the ticker symbol and try again.")

        st.subheader(f"Current Price of {ticker.upper()}: ${price:.2f}")

        yf_range = display_to_yf[chart_range_display]
        interval = range_to_interval[yf_range]
        hist = stock.history(period=yf_range, interval=interval)

        if hist.empty:
            st.warning("No historical data available.")
        else:
            if yf_range in ["1d", "5d"]:
                hist = hist.between_time("09:30", "20:00")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode="lines",
                name="Close Price"
            ))

            fig.update_layout(
                title=f"{ticker.upper()} Historical Prices",
                xaxis_title="Time",
                yaxis_title="Price ($)",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # ---- Implied Volatility Estimation ----
        if st.button("Estimate Implied Volatility"):
            try:
                if strike == 0 or T == 0 or r == 0 or market_price == 0:
                    st.error("Please fill in all inputs before estimating implied volatility.")
                else:
                    iv = implied_volatility(S=price, K=strike, T=T, r=r, market_price=market_price, option_type=option_type)
                    if iv is not None:
                        st.markdown(
                            f"""
                            <div style='
                                background-color: #a8d8f0;
                                padding: 1rem;
                                border-radius: 0.5rem;
                                font-weight: bold;
                                color: black;
                                font-size: 16px;
                                margin-top: 1rem;
                            '>
                                <b>Implied Volatility ({option_display})</b>: {iv * 100:.2f}%
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.error("Could not estimate implied volatility. Try adjusting inputs.")
            except Exception:
                st.error("Error: Estimation failed. Please check inputs and try again.")

    except Exception:
        st.error("Error: Could not retrieve stock data. Please check the ticker symbol and try again.")
