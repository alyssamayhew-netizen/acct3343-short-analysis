
import streamlit as st
import yfinance as yf
import pandas as pd

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

# --- Financial field inspection ---

from financial_analysis import inspect_company_fields

st.divider()
st.header("Financial Field Inspection")

selected_ticker = st.selectbox(
    "Choose a company to inspect",
    options=["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"],
)

if st.button("Inspect available fields"):
    with st.spinner("Inspecting financial data..."):
        fields = inspect_company_fields(selected_ticker)

    if isinstance(fields, dict):
        st.error(fields.get("field", "Unable to retrieve fields."))
    elif fields:
        st.success(f"Found {len(fields)} financial fields!")
        st.dataframe(fields, use_container_width=True)
    else:
        st.warning("No financial fields were returned.")

# --- Metric field coverage report ---

from financial_analysis import check_metric_field_coverage

st.divider()
st.header("Seven-Metric Field Coverage")

if st.button("Check fields for all five companies"):
    coverage_results = []

    with st.spinner("Checking all five companies..."):
        for ticker in ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]:
            coverage_results.extend(
                check_metric_field_coverage(ticker)
            )

    coverage_df = pd.DataFrame(coverage_results)

    st.dataframe(coverage_df, use_container_width=True)

    summary = (
        coverage_df.groupby("metric")["available"]
        .agg(["sum", "count"])
        .reset_index()
    )
    summary["coverage"] = (
        summary["sum"].astype(str)
        + " of "
        + summary["count"].astype(str)
        + " required fields"
    )

    st.subheader("Coverage Summary")
    st.dataframe(summary, use_container_width=True)

# --- SNOA input inspector ---

from financial_analysis import inspect_snoa_inputs

st.divider()
st.header("SNOA Input Inspector")

snoa_ticker = st.selectbox(
    "Choose a company to inspect for SNOA",
    options=["CTC-A.TO", "SHOP.TO", "CNR.TO"],
    key="snoa_ticker",
)

if st.button("Inspect SNOA inputs"):
    with st.spinner("Checking the latest balance sheet..."):
        snoa_results = inspect_snoa_inputs(snoa_ticker)

    if isinstance(snoa_results, dict):
        st.error(snoa_results.get("error", "Unable to retrieve data."))
    else:
        st.dataframe(
            pd.DataFrame(snoa_results),
            use_container_width=True,
        )

# --- SNOA equity input test ---

from financial_analysis import get_snoa_equity_inputs

st.divider()
st.header("SNOA Equity Input Test")

equity_ticker = st.selectbox(
    "Choose a company",
    options=["CTC-A.TO", "SHOP.TO", "CNR.TO"],
    key="equity_ticker",
)

if st.button("Check equity inputs"):
    with st.spinner("Retrieving equity data..."):
        equity_data = get_snoa_equity_inputs(equity_ticker)

    st.dataframe(
        pd.DataFrame([equity_data]),
        use_container_width=True,
    )

# --- Equity reconciliation diagnostic ---

from financial_analysis import inspect_equity_reconciliation

st.divider()
st.header("Minority Interest Reconciliation")

reconciliation_ticker = st.selectbox(
    "Choose a company for equity reconciliation",
    options=["SHOP.TO", "CNR.TO"],
    key="reconciliation_ticker",
)

if st.button("Inspect equity reconciliation"):
    with st.spinner("Comparing equity fields..."):
        reconciliation = inspect_equity_reconciliation(
            reconciliation_ticker
        )

    if isinstance(reconciliation, dict):
        st.error(reconciliation.get("error", "Unable to retrieve data."))
    else:
        st.dataframe(
            pd.DataFrame(reconciliation),
            use_container_width=True,
        )

# --- SNOA calculation test ---

from financial_analysis import calculate_snoa

st.divider()
st.header("SNOA Calculation Test")

if st.button("Calculate SNOA for all five companies"):
    snoa_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating SNOA..."):
        for ticker in tickers:
            snoa_results.append(calculate_snoa(ticker))

    snoa_df = pd.DataFrame(snoa_results)

    st.dataframe(snoa_df, use_container_width=True)

    calculated_count = (
        snoa_df["status"] == "Calculated"
    ).sum()

    st.write(
        f"SNOA calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )

# --- Book-to-Market calculation test ---

from financial_analysis import calculate_book_to_market

st.divider()
st.header("Book-to-Market (BM) Calculation Test")

if st.button("Calculate BM for all five companies"):
    bm_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating Book-to-Market..."):
        for ticker in tickers:
            bm_results.append(calculate_book_to_market(ticker))

    bm_df = pd.DataFrame(bm_results)

    st.dataframe(bm_df, use_container_width=True)

    calculated_count = (
        bm_df["status"] == "Calculated"
    ).sum()

    st.write(
        f"BM calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )

# --- Gross Profitability calculation test ---

from financial_analysis import calculate_gross_profitability

st.divider()
st.header("Gross Profitability (GP) Calculation Test")

if st.button("Calculate GP for all five companies"):
    gp_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating Gross Profitability..."):
        for ticker in tickers:
            gp_results.append(calculate_gross_profitability(ticker))

    gp_df = pd.DataFrame(gp_results)

    st.dataframe(gp_df, use_container_width=True)

    calculated_count = (
        gp_df["status"] == "Calculated"
    ).sum()

    st.write(
        f"GP calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )

# --- Cash Flow from Assets (CFOA) calculation test ---

from financial_analysis import calculate_cfoa

st.divider()
st.header("Cash Flow from Assets (CFOA) Calculation Test")

if st.button("Calculate CFOA for all five companies"):
    cfoa_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating CFOA..."):
        for ticker in tickers:
            cfoa_results.append(calculate_cfoa(ticker))

    cfoa_df = pd.DataFrame(cfoa_results)

    st.dataframe(cfoa_df, use_container_width=True)

    calculated_count = (
        cfoa_df["status"] == "Calculated"
    ).sum()

    st.write(
        f"CFOA calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )

# --- Return on Capital (ROC) calculation test ---

from financial_analysis import calculate_roc

st.divider()
st.header("Return on Capital (ROC) Calculation Test")

if st.button("Calculate ROC for all five companies"):
    roc_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating Return on Capital..."):
        for ticker in tickers:
            roc_results.append(calculate_roc(ticker))

    roc_df = pd.DataFrame(roc_results)

    st.dataframe(roc_df, use_container_width=True)

    calculated_count = (roc_df["status"] == "Calculated").sum()

    st.write(
        f"ROC calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )
