import streamlit as st
import yfinance as yf
import numpy as np
import math
import plotly.graph_objects as go

# ---- Binomial Tree Function ----
def binomial_tree(S, K, T, r, sigma, N, option_type='call'):
    dt = T / N
    u = math.exp(sigma * math.sqrt(dt))
    d = 1 / u
    p = (math.exp(r * dt) - d) / (u - d)

    option = np.zeros((N + 1, N + 1))
    for j in range(N + 1):
        ST = S * (u ** (N - j)) * (d ** j)
        if option_type == 'call':
            option[N, j] = max(ST - K, 0)
        else:
            option[N, j] = max(K - ST, 0)

    for i in range(N - 1, -1, -1):
        for j in range(i + 1):
            option[i, j] = math.exp(-r * dt) * (p * option[i + 1, j] + (1 - p) * option[i + 1, j + 1])

    return option[0, 0]

# ---- Page Setup ----
st.set_page_config(page_title="Binomial Tree", layout="centered")
st.title("Binomial Tree Option Pricing")
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
        Stepwise tree-based model using Cox-Ross-Rubinstein method.
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Sidebar Inputs ----
with st.sidebar:
    ticker = st.text_input("Stock Ticker")
    strike = st.number_input("Strike Price ($)", min_value=0.0, format="%.2f")
    T_days = st.number_input("Time to Maturity (Days)", min_value=1)
    r_percent = st.number_input("Risk-Free Rate (%)", min_value=0.0, format="%.2f")
    sigma_percent = st.number_input("Volatility (%)", min_value=0.1, format="%.2f")
    steps = st.number_input("Steps (N)", min_value=1)
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

        # ---- Option Pricing ----
        if st.button("Calculate Option Price"):
            try:
                latest_price = stock.info.get("regularMarketPrice")
                if latest_price is None:
                    raise ValueError("Stock not found or unavailable. Please re-check the ticker.")

                if strike == 0 or T == 0 or r == 0 or sigma == 0 or steps == 0:
                    st.error("Please fill in all inputs before calculating the option price.")
                else:
                    bt_price = binomial_tree(
                        S=latest_price, K=strike, T=T, r=r, sigma=sigma,
                        N=int(steps), option_type=option_type
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
                            <b>{option_display} Option Price (Binomial Tree)</b>: ${bt_price:.2f}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            except Exception:
                st.error("Error: Unable to calculate. Please check your inputs and try again.")

    except Exception:
        st.error("Error: Could not retrieve stock data. Please check the ticker symbol and try again.")
