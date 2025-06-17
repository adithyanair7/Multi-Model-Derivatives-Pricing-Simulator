import streamlit as st

st.set_page_config(page_title="Home", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"]  {
    background-color: #1a1a1a;
    font-family: 'Georgia', serif;
    color: #f9f9f9;
}
.container {
    max-width: 1000px;
    margin: auto;
    padding: 2rem;
    background-color: #2a2a2a;
    border-radius: 12px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.2);
}
h1 {
    font-size: 2.75rem;
    color: #ffffff;
    font-weight: 700;
    font-family: 'Georgia', serif;
}
p, .stMarkdown {
    font-size: 1.15rem;
    line-height: 1.6;
    color: #f0f0f0;
    font-family: 'Georgia', serif;
}
.stButton > button {
    width: 100%;
    background-color: #2e2e2e;
    color: white;
    font-weight: 700;
    font-size: 1.2rem;
    padding: 1rem 1.5rem;
    border: 2px solid black;
    border-radius: 12px;
    margin-top: 1rem;
    transition: all 0.2s ease-in-out;
    font-family: 'Georgia', serif;
}
.stButton > button:hover {
    background-color: #444444;
    transform: translateY(-1px);
    border-color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    st.markdown("""
    # Options Pricing Calculator

    #### Select your preferred pricing model below:
    """)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Black-Scholes Pricer (European)"):
            st.switch_page("pages/1_Black-Scholes Pricer.py")
        if st.button("Binomial Tree Pricer"):
            st.switch_page("pages/3_Binomial Tree Pricer.py")

    with col2:
        if st.button("Monte Carlo Pricer (American)"):
            st.switch_page("pages/2_Monte Carlo Pricer.py")
        if st.button("Implied Volatility Estimator"):
            st.switch_page("pages/4_Implied Volatility Estimator.py")
