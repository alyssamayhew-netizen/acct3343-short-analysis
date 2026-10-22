import streamlit as st
import yfinance as yf
import pandas as pd

from financial_analysis import (
    calculate_roc,
    calculate_ey,
    calculate_book_to_market,
    calculate_gross_profitability,
    calculate_cfoa,
    calculate_snoa,
    calculate_altman_z,
)

# --- Companies used throughout the app ---

COMPANY_TICKERS = [
    "SHOP.TO",
    "CTC-A.TO",
    "CNR.TO",
    "ENB.TO",
    "FTS.TO",
    "CP.TO",
    "CNQ.TO",
    "SU.TO",
    "ATD.TO",
    "DOL.TO",
    "MG.TO",
    "TRI.TO",
    "WCN.TO",
    "BCE.TO",
    "CU.TO",
]
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

# --- App View Selector ---

app_mode = st.radio(
    "Choose a view",
    ["Dashboard", "Stock Comparison"],
    horizontal=True,
    key="app_mode",
)

# --- Stock Comparison View ---

if app_mode == "Stock Comparison":
    st.divider()
    st.header("⚖️ Stock Comparison")
    st.write(
        "Compare two companies using the same seven financial "
        "metrics. Unavailable results are shown clearly."
    )

    tickers = COMPANY_TICKERS


    col_a, col_b = st.columns(2)
    
    with col_a:
        ticker_a = st.selectbox(
            "First company",
            options=tickers,
            index=0,
            key="comparison_ticker_a",
        )

    with col_b:
        ticker_b = st.selectbox(
            "Second company",
            options=tickers,
            index=1,
            key="comparison_ticker_b",
        )

    if ticker_a == ticker_b:
        st.warning("Please select two different companies.")
        st.stop()

    comparison_metrics = [
        (
            "Return on Capital (ROC)",
            calculate_roc,
            "roc",
            "Higher is generally better: more operating profit per dollar of capital.",
        ),
        (
            "Earnings Yield (EY)",
            calculate_ey,
            "ey",
            "Higher generally means more operating earnings relative to enterprise value.",
        ),
        (
            "Book-to-Market (BM)",
            calculate_book_to_market,
            "book_to_market",
            "Higher can suggest a value opportunity, but may also reflect financial trouble.",
        ),
        (
            "Gross Profitability",
            calculate_gross_profitability,
            "gross_profitability",
            "Higher generally means more gross profit relative to total assets.",
        ),
        (
            "Cash Flow from Operations (CFOA)",
            calculate_cfoa,
            "cfoa",
            "Higher generally indicates stronger cash generation relative to assets.",
        ),
        (
            "Spread in Net Operating Assets (SNOA)",
            calculate_snoa,
            "snoa",
            "Lower can be favourable, as it indicates less net operating assets relative to total assets.",
        ),
        (
            "Altman Z-Score",
            calculate_altman_z,
            "altman_z",
            "Higher generally indicates lower estimated financial-distress risk.",
        ),
    ]

    def get_comparison_value(calculate_function, ticker, value_key):
        try:
            result = calculate_function(ticker)

            if result.get("status") == "Calculated":
                value = result.get(value_key)

                if value is not None and pd.notna(value):
                    return f"{value:,.4f}"

        except Exception:
            pass

        return "Unavailable"


    comparison_results = []

    with st.spinner("Calculating both companies' financial metrics..."):
        for metric_name, calculate_function, value_key, explanation in comparison_metrics:
            value_a = get_comparison_value(
                calculate_function, ticker_a, value_key
            )
            value_b = get_comparison_value(
                calculate_function, ticker_b, value_key
            )
            comparison_results.append(
                (metric_name, value_a, value_b, explanation)
            )

    favourable_a = 0
    favourable_b = 0
    ties = 0
    metrics_compared = 0

    for metric_name, value_a, value_b, explanation in comparison_results:
        if metric_name == "Book-to-Market (BM)":
            continue

        if value_a == "Unavailable" or value_b == "Unavailable":
            continue

        try:
            number_a = float(str(value_a).replace(",", ""))
            number_b = float(str(value_b).replace(",", ""))
        except (ValueError, TypeError):
            continue

        metrics_compared += 1

        if abs(number_a - number_b) < 0.0001:
            ties += 1
        elif metric_name == "Spread in Net Operating Assets (SNOA)":
            if number_a < number_b:
                favourable_a += 1
            else:
                favourable_b += 1
        elif number_a > number_b:
            favourable_a += 1
        else:
            favourable_b += 1

    st.subheader("📊 Overall Comparison Summary")

    left, right = st.columns(2)

    with left:
        st.metric(f"{ticker_a} — Favourable Indicators", favourable_a)

    with right:
        st.metric(f"{ticker_b} — Favourable Indicators", favourable_b)

    st.caption(
        f"Compared {metrics_compared} of the six directional metrics. "
        f"Tied metrics: {ties}. Book-to-Market is excluded because a higher "
        "value is not always better. Unavailable metrics are excluded. "
        "This is a screening aid, not an investment recommendation."
    )

    if metrics_compared == 0:
        st.info("Not enough comparable metrics to summarize these companies.")
    elif favourable_a > favourable_b:
        st.write(f"**{ticker_a} has more favourable indicators.**")
    elif favourable_b > favourable_a:
        st.write(f"**{ticker_b} has more favourable indicators.**")
    else:
        st.write("**Mixed results:** neither company has more favourable indicators.")

    st.divider()

    for metric_name, value_a, value_b, explanation in comparison_results:
        with st.container(border=True):
            st.markdown(f"**{metric_name}**")

            left, right = st.columns(2)

            with left:
                st.metric(ticker_a, value_a)

            with right:
                st.metric(ticker_b, value_b)

            st.caption(explanation)

    st.caption(
        "These metrics are screening indicators, not guarantees. "
        "Compare companies in context, and remember that some "
        "formulas may be less suitable for certain industries."
    )

    st.stop()

st.divider()

st.header("Company Financial Analysis")

st.write(
    "Enter a stock ticker to view its seven financial formula results."
)

# --- Company Financial Analysis ---

ticker_symbol = st.text_input(
    "Stock ticker",
    value="RY.TO",
    help="Examples: RY.TO, TD.TO, ENB.TO, CNR.TO, SHOP.TO"
).strip().upper()

if st.button("Analyze Company"):
    if not ticker_symbol:
        st.warning("Please enter a stock ticker.")
    else:
        try:
            with st.spinner("Calculating financial metrics..."):
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
                st.caption(f"Ticker: {ticker_symbol}")



                metrics = [
                    (
                        "Return on Capital (ROC)",
                        calculate_roc,
                        "roc",
                        "Formula: EBIT / (Net PPE + Net Working Capital). "
                        "Higher is generally better."
                    ),
                    (
                        "Earnings Yield (EY)",
                        calculate_ey,
                        "ey",
                        "Formula: EBIT / Enterprise Value. "
                        "Higher generally means more operating earnings "
                        "relative to enterprise value."
                    ),
                    (
                        "Book-to-Market (BM)",
                        calculate_book_to_market,
                        "book_to_market",
                        "Formula: Book Value / Market Capitalization. "
                        "Higher may indicate value, but can also indicate distress."
                    ),
                    (
                        "Gross Profitability",
                        calculate_gross_profitability,
                        "gross_profitability",
                        "Formula: (Revenue - Cost of Goods Sold) / Total Assets. "
                        "Higher generally indicates more gross profit relative to assets."
                    ),
                    (
                        "Cash Flow from Operations (CFOA)",
                        calculate_cfoa,
                        "cfoa",
                        "Formula: Sum of four annual free cash flow values / Total Assets. "
                        "Higher generally indicates stronger cash generation."
                    ),
                    (
                        "Spread in Net Operating Assets (SNOA)",
                        calculate_snoa,
                        "snoa",
                        "Formula: (Operating Assets - Operating Liabilities) / Total Assets. "
                        "Lower can be favourable, depending on the industry."
                    ),
                    (
                        "Altman Z-Score",
                        calculate_altman_z,
                        "altman_z",
                        "A financial-distress screening measure. Higher generally "
                        "indicates lower estimated distress risk."
                    ),
                ]

                for metric_name, calculate_function, value_key, explanation in metrics:
                    try:
                        result = calculate_function(ticker_symbol)

                        with st.container(border=True):
                            if result.get("status") == "Calculated":
                                value = result.get(value_key)

                                if value is not None and pd.notna(value):
                                    st.metric(
                                        label=metric_name,
                                        value=f"{value:,.4f}",
                                        help=explanation,
                                    )
                                else:
                                    st.markdown(f"**{metric_name}**")
                                    st.warning(
                                        "This formula returned no usable value "
                                        "for this company."
                                    )
                            else:
                                st.markdown(f"**{metric_name}**")
                                st.warning(
                                    result.get(
                                        "details",
                                        result.get(
                                            "status",
                                            "Result unavailable"
                                        )
                                    )
                                )

                    except Exception as e:
                        st.markdown(f"**{metric_name}**")
                        st.warning(
                            "This formula could not be calculated for this company."
                        )
                        st.caption(f"Technical details: {e}")

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
    options=COMPANY_TICKERS
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
    options=COMPANY_TICKERS,
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
    tickers = COMPANY_TICKERS,
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

    tickers = COMPANY_TICKERS

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

# --- Earnings Yield (EY) calculation test ---

from financial_analysis import calculate_ey

st.divider()
st.header("Earnings Yield (EY) Calculation Test")

if st.button("Calculate EY for all five companies"):
    ey_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating Earnings Yield..."):
        for ticker in tickers:
            ey_results.append(calculate_ey(ticker))

    ey_df = pd.DataFrame(ey_results)

    st.dataframe(ey_df, use_container_width=True)

    calculated_count = (ey_df["status"] == "Calculated").sum()

    st.write(
        f"EY calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )

# --- Altman Z-score calculation test ---

from financial_analysis import calculate_altman_z

st.divider()
st.header("Altman Z-Score Calculation Test")

if st.button("Calculate Altman Z-score for all five companies"):
    z_results = []

    tickers = ["ENB.TO", "CNR.TO", "SHOP.TO", "CTC-A.TO", "FTS.TO"]

    with st.spinner("Calculating Altman Z-scores..."):
        for ticker in tickers:
            z_results.append(calculate_altman_z(ticker))

    z_df = pd.DataFrame(z_results)

    st.dataframe(z_df, use_container_width=True)

    calculated_count = (z_df["status"] == "Calculated").sum()

    st.write(
        f"Altman Z-score calculated successfully for "
        f"{calculated_count} of {len(tickers)} companies."
    )
st.subheader("Temporary Market Cap Diagnostic")

import yfinance as yf

ticker = yf.Ticker("SHOP.TO")

try:
    info = ticker.get_info()
    st.write("Summary marketCap:", info.get("marketCap"))
except Exception as e:
    st.write("Summary error:", str(e))

try:
    fast_info = ticker.fast_info
    st.write("Fast info market_cap:", fast_info.get("market_cap"))
except Exception as e:
    st.write("Fast info error:", str(e))
st.subheader("Yahoo Finance Connection Check")

ticker = yf.Ticker("SHOP.TO")

try:
    history = ticker.history(period="5d")
    st.write("Price history rows:", len(history))
    st.write(history.tail(2))
except Exception as e:
    st.write("Price history error:", str(e))

try:
    balance_sheet = ticker.balance_sheet
    st.write("Balance sheet rows:", list(balance_sheet.index[:5]))
except Exception as e:
    st.write("Balance sheet error:", str(e))

# --- BUY / SELL Rankings ---

st.divider()
st.title("📈 Stock Analysis Dashboard")
st.write(
    "Compare companies, discover potential BUY and SELL candidates, "
    "and explore seven financial metrics."
)

st.title("🏆 Stock Rankings")

tickers = COMPANY_TICKERS

ranking_metrics = [
    ("ROC", calculate_roc, "roc", False),
    ("EY", calculate_ey, "ey", False),
    ("BM", calculate_book_to_market, "book_to_market", False),
    (
        "Gross Profitability",
        calculate_gross_profitability,
        "gross_profitability",
        False,
    ),
    ("CFOA", calculate_cfoa, "cfoa", False),
    ("SNOA", calculate_snoa, "snoa", True),
    ("Altman Z", calculate_altman_z, "altman_z", False),
]


results = {}

with st.spinner("Calculating company metrics..."):
    for ticker in tickers:
        results[ticker] = {}

        for name, function, key, lower_is_better in ranking_metrics:
            try:
                result = function(ticker)
                value = result.get(key)

                if (
                    result.get("status") == "Calculated"
                    and isinstance(value, (int, float))
                    and value == value
                ):
                    results[ticker][name] = float(value)

            except Exception:
                pass

# --- Financial Metric Filters ---

st.divider()
st.subheader("🎚️ Financial Metric Filters")
st.caption(
    "Adjust the acceptable range for each metric. "
    "Companies outside a selected range are excluded from the rankings."
)

metric_ranges = {}
filter_columns = st.columns(2)

for i, (name, function, key, lower_is_better) in enumerate(ranking_metrics):
    available_values = [
        results[ticker][name]
        for ticker in tickers
        if name in results[ticker]
    ]

    with filter_columns[i % 2]:
        if available_values:
            observed_min = min(available_values)
            observed_max = max(available_values)

            if observed_min == observed_max:
                padding = max(abs(observed_min) * 0.05, 0.01)
                slider_min = observed_min - padding
                slider_max = observed_max + padding
            else:
                slider_min = observed_min
                slider_max = observed_max

            step = (slider_max - slider_min) / 100

            selected_range = st.slider(
                f"{name} acceptable range",
                min_value=float(slider_min),
                max_value=float(slider_max),
                value=(float(slider_min), float(slider_max)),
                step=float(step),
                key=f"filter_{key}",
            )

            metric_ranges[name] = selected_range

        else:
            st.slider(
                f"{name} acceptable range",
                min_value=0.0,
                max_value=1.0,
                value=(0.0, 1.0),
                disabled=True,
                key=f"filter_{key}",
            )
            st.caption("No values available for this metric.")
            metric_ranges[name] = (float("-inf"), float("inf"))

# --- Apply Filters ---

eligible_tickers = []

for ticker in tickers:
    matches_filters = True

    for name, selected_range in metric_ranges.items():
        if name in results[ticker]:
            value = results[ticker][name]

            if value < selected_range[0] or value > selected_range[1]:
                matches_filters = False
                break

    if matches_filters:
        eligible_tickers.append(ticker)

st.caption(
    f"{len(eligible_tickers)} of {len(tickers)} companies "
    "currently meet the selected metric ranges."
)

# --- Recalculate Rankings Using Eligible Companies ---

metric_scores = {ticker: [] for ticker in eligible_tickers}

for name, function, key, lower_is_better in ranking_metrics:
    available = [
        (ticker, results[ticker][name])
        for ticker in eligible_tickers
        if name in results[ticker]
    ]

    available.sort(
        key=lambda item: item[1],
        reverse=not lower_is_better,
    )

    for position, (ticker, value) in enumerate(available):
        score = (
            1.0
            if len(available) == 1
            else 1 - position / (len(available) - 1)
        )
        metric_scores[ticker].append(score)

rows = []

for ticker in tickers:
    values = results[ticker]
    scores = metric_scores.get(ticker, [])

    ranking_score = (
        round(sum(scores) / len(scores), 3)
        if ticker in eligible_tickers and len(values) >= 4 and scores
        else None
    )

    rows.append({
        "Ticker": ticker,
        "Metrics Available": len(values),
        "Ranking Score": ranking_score,
    })

ranked_rows = [
    row for row in rows
    if row["Ranking Score"] is not None
]

ranked_rows.sort(
    key=lambda row: row["Ranking Score"],
    reverse=True,
)

for index, row in enumerate(ranked_rows):
    if index < 2 and len(ranked_rows) >= 4:
        row["Signal"] = "Potential BUY"
    elif index >= len(ranked_rows) - 2 and len(ranked_rows) >= 4:
        row["Signal"] = "Potential SELL"
    else:
        row["Signal"] = "Middle-ranked"

for row in rows:
    if row["Ranking Score"] is None:
        if row["Ticker"] not in eligible_tickers:
            row["Signal"] = "Filtered out"
        else:
            row["Signal"] = "Insufficient data"

# --- BUY / SELL Highlights ---

st.subheader("🟢 Top BUY Candidates")
buy_candidates = [
    row for row in ranked_rows
    if row["Signal"] == "Potential BUY"
]

if buy_candidates:
    buy_columns = st.columns(len(buy_candidates))

    for column, row in zip(buy_columns, buy_candidates):
        with column:
            st.success(
                f"**{row['Ticker']}**\n\n"
                f"Ranking Score: {row['Ranking Score']:.3f}\n\n"
                f"Metrics Available: {row['Metrics Available']}/7"
            )
else:
    st.info("No BUY candidates with sufficient data.")

st.subheader("🔴 Top SELL Candidates")
sell_candidates = [
    row for row in ranked_rows
    if row["Signal"] == "Potential SELL"
]

if sell_candidates:
    sell_columns = st.columns(len(sell_candidates))

    for column, row in zip(sell_columns, sell_candidates):
        with column:
            st.error(
                f"**{row['Ticker']}**\n\n"
                f"Ranking Score: {row['Ranking Score']:.3f}\n\n"
                f"Metrics Available: {row['Metrics Available']}/7"
            )
else:
    st.info("No SELL candidates with sufficient data.")


def colour_signal(value):
    if value == "Potential BUY":
        return "background-color: #C6EFCE; color: #006100"
    elif value == "Potential SELL":
        return "background-color: #FFC7CE; color: #9C0006"
    elif value == "Middle-ranked":
        return "background-color: #FFEB9C; color: #9C6500"
    else:
        return ""

styled_rows = (
    __import__("pandas")
    .DataFrame(rows)
    .style
    .map(colour_signal, subset=["Signal"])
    .format({"Ranking Score": "{:.3f}"}, na_rep="—")
)

st.dataframe(
    styled_rows,
    use_container_width=True,
    hide_index=True,
    height=400,
)

st.caption(
    "Higher ROC, EY, BM, gross profitability, CFOA and Altman Z "
    "scores rank favourably; lower SNOA ranks favourably. "
    "Scores are relative to this sample of companies, not "
    "personalized investment advice."
)
