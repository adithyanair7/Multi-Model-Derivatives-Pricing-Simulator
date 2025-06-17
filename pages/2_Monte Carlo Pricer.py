import streamlit as st
import yfinance as yf
import numpy as np
import math
import plotly.graph_objects as go
import requests
from urllib.error import HTTPError

# ---- LSM Monte Carlo Function ----
def lsm_american_option_price(S0, K, T, r, sigma, option_type='call', simulations=10000, steps=100):
    dt = T / steps
    discount = math.exp(-r * dt)
    payoff = np.zeros(simulations)
    paths = np.zeros((simulations, steps + 1))
    paths[:, 0] = S0

    for t in range(1, steps + 1):
        z = np.random.standard_normal(simulations)
        paths[:, t] = paths[:, t - 1] * np.exp((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)

    if option_type == 'call':
        payoff = np.maximum(paths[:, -1] - K, 0)
    else:
        payoff = np.maximum(K - paths[:, -1], 0)

    for t in range(steps - 1, 0, -1):
        if option_type == 'call':
            payoff *= discount  # only discount, no early exercise for calls
            continue

        itm = np.where(paths[:, t] < K)[0]
        if len(itm) == 0:
            continue
        X = paths[itm, t]
        Y = payoff[itm] * discount
        A = np.vstack([np.ones(len(X)), X, X**2]).T
        coeffs = np.linalg.lstsq(A, Y, rcond=None)[0]
        continuation_value = coeffs[0] + coeffs[1]*X + coeffs[2]*X**2
        exercise_value = np.maximum(K - paths[itm, t], 0)
        exercise = exercise_value > continuation_value
        payoff[itm[exercise]] = exercise_value[exercise]
        payoff[~np.isin(np.arange(simulations), itm[exercise])] *= discount

    return np.mean(payoff) * math.exp(-r * dt)

# ---- Page Setup ----
st.set_page_config(page_title="Monte Carlo American", layout="centered")
st.title("Monte Carlo Option Pricer")
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
        Simulation-based model for pricing American-style options.
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Sidebar Inputs ----
with st.sidebar:
    ticker = st.text_input("Stock Ticker")
    strike = st.number_input("Strike Price ($)", min_value=0.0, format="%.2f")
    T = st.number_input("Time to Maturity (Years)", min_value=0.0, format="%.2f")
    r_percent = st.number_input("Risk-Free Rate (%)", min_value=0.0, format="%.2f")
    sigma_percent = st.number_input("Volatility (%)", min_value=0.0, format="%.2f")

    # Capitalized dropdown, mapped to lowercase values
    option_label_map = {"Call": "call", "Put": "put"}
    option_display = st.selectbox("Option Type", list(option_label_map.keys()))
    option_type = option_label_map[option_display]

    simulations = st.number_input("Simulations", min_value=1000, step=1000)
    steps = st.number_input("Steps per Path", min_value=10)

    chart_range_display = st.selectbox(
        "Chart Range",
        options=["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "Max"],
        index=3
    )

# ---- Convert %
r = r_percent / 100
sigma = sigma_percent / 100

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

        # ---- Run Monte Carlo ----
        if st.button("Run Monte Carlo Simulation"):
            try:
                latest_price = stock.info.get("regularMarketPrice")
                if latest_price is None:
                    raise ValueError("Stock not found or unavailable. Please re-check the ticker.")

                if strike == 0 or T == 0 or r == 0 or sigma == 0 or simulations == 0 or steps == 0:
                    st.error("Please fill in all inputs before running the simulation.")
                else:
                    mc_price = lsm_american_option_price(
                        S0=latest_price, K=strike, T=T, r=r, sigma=sigma,
                        option_type=option_type, simulations=simulations, steps=int(steps)
                    )
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
                            <b>{option_display} Option Price (LSM Monte Carlo)</b>: ${mc_price:.2f}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception:
                st.error("Error: Stock not found or price could not be retrieved. Please check the ticker symbol and try again.")

    except (HTTPError, requests.exceptions.RequestException, ValueError, KeyError):
        st.error("Error: Stock not found. Please check the ticker symbol and try again.")
    except Exception:
        st.error("An unexpected error occurred while retrieving the stock data.")
