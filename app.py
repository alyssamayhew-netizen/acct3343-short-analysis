
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Short-Term Stock Analysis",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Short-Term Stock Analysis")
st.write("ACCT 3343 — Financial Statement Analysis")

st.markdown("""
Welcome to our stock analysis app!

This tool will compare publicly traded companies
using financial metrics to identify potential BUY
and SELL candidates.
""")

st.divider()

st.header("🔎 Company Lookup")

st.write(
    "Enter a stock ticker to explore its financial "
    "information and historical share price."
)

ticker_symbol = st.text_input(
    "Stock ticker",
    value="RY.TO",
    help="Examples: RY.TO, TD.TO, ENB.TO, CNR.TO, SHOP.TO"
).strip().upper()

if st.button("Retrieve Financial Data"):
    if not ticker_symbol:
        st.warning("Please enter a stock ticker.")
    else:
        try:
            with st.spinner("Retrieving data from Yahoo Finance..."):
                company = yf.Ticker(ticker_symbol)
                info = company.get_info()

                company_name = (
                    info.get("longName")
                    or info.get("shortName")
                )

                if not company_name:
                    st.error(
                        "Company information wasn't available. "
                        "Check the ticker and try again."
                    )
                    st.stop()

                st.subheader(company_name)

                col1, col2, col3 = st.columns(3)

                price = (
                    info.get("currentPrice")
                    or info.get("regularMarketPrice")
                )

                with col1:
                    st.metric(
                        "Latest Available Price",
                        f"{price:,.2f}" if price is not None
                        else "Unavailable",
                        help="Price may be delayed and is not guaranteed to be real-time."
                    )

                with col2:
                    market_cap = info.get("marketCap")
                    st.metric(
                        "Market Capitalization",
                        f"{market_cap:,.0f}"
                        if market_cap is not None
                        else "Unavailable"
                    )

                with col3:
                    pe_ratio = info.get("trailingPE")
                    st.metric(
                        "Trailing P/E Ratio",
                        f"{pe_ratio:.2f}"
                        if pe_ratio is not None
                        else "Unavailable"
                    )

                st.subheader("Historical Share Price")

                prices = company.history(period="1y")

                if not prices.empty:
                    st.line_chart(prices["Close"])
                else:
                    st.info("No historical price data was returned.")

                st.subheader("Financial Statements")

                statements = [
                    ("Income Statement", company.income_stmt),
                    ("Balance Sheet", company.balance_sheet),
                    ("Cash Flow Statement", company.cashflow),
                ]

                for title, statement in statements:
                    with st.expander(title):
                        if not statement.empty:
                            st.dataframe(
                                statement,
                                use_container_width=True
                            )
                        else:
                            st.info(
                                "No data available for this statement."
                            )

        except Exception as e:
            st.error(
                "We couldn't retrieve the data. "
                "Please check the ticker or try again later."
            )
            st.caption(f"Technical details: {e}")

st.divider()

st.info(
    "Our app is under construction. "
    "Financial ratios, company comparisons, and stock "
    "screening features are coming soon!"
)

# --- Financial data coverage test ---

from financial_analysis import test_company_universe

st.divider()
st.header("Financial Data Coverage Test")

st.write(
    "Checking which financial statements Yahoo Finance provides "
    "for our initial five Canadian companies."
)

if st.button("Check financial data"):
    with st.spinner("Checking Yahoo Finance..."):
        results = test_company_universe()

    st.dataframe(results, use_container_width=True)

    if results["status"].eq("Retrieved").all():
        st.success("The data retrieval process completed for all five companies.")
    else:
        st.warning(
            "Some companies could not be retrieved. "
            "We'll investigate the results before calculating ratios."
        )
