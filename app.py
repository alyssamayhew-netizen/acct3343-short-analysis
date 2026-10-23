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

@st.cache_data(ttl=86400)
def load_company_universe(cache_version):
    companies = pd.read_csv("company_universe.csv")
    companies = companies.dropna(subset=["ticker"])
    return companies

company_universe = load_company_universe("universe-v2-restore-ry")
COMPANY_TICKERS = company_universe["ticker"].astype(str).tolist()
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

ticker_symbol = st.selectbox(
    "Search for a company by ticker",
    options=COMPANY_TICKERS,
    index=COMPANY_TICKERS.index("RY.TO") if "RY.TO" in COMPANY_TICKERS else 0,
    help="Start typing a ticker to find it in the 1,000-company universe."
)

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


if "rankings_requested" not in st.session_state:
    st.session_state["rankings_requested"] = False

if not st.session_state["rankings_requested"]:
    st.info(
        "The full rankings cover all 1,000 companies and can take several minutes "
        "to calculate the first time. Company Lookup and Stock Comparison are "
        "available above while you decide when to start."
    )
    if st.button("Calculate rankings for all 1,000 companies", type="primary"):
        st.session_state["rankings_requested"] = True
        st.rerun()
    st.stop()


@st.cache_data(ttl=21600, show_spinner="Calculating company metrics for the full stock universe...")
def calculate_ranking_results(ticker_list, cache_version):
    """Calculate rankings once, then reuse them during filter and layout reruns.

    cache_version deliberately invalidates results from the older,
    request-heavy calculation pipeline.
    """
    calculated_results = {}

    for ticker in ticker_list:
        calculated_results[ticker] = {}

        for name, function, key, lower_is_better in ranking_metrics:
            try:
                result = function(ticker)
                value = result.get(key)

                if (
                    result.get("status") == "Calculated"
                    and isinstance(value, (int, float))
                    and value == value
                ):
                    calculated_results[ticker][name] = float(value)

            except Exception:
                pass

    return calculated_results


results = calculate_ranking_results(tuple(tickers), "shared-data-cache-v1")

# Make calculation coverage visible instead of silently hiding failed metrics.
companies_with_metrics = sum(bool(results.get(ticker)) for ticker in tickers)
st.subheader("📊 Calculation Coverage")
st.write(
    f"At least one metric calculated for **{companies_with_metrics} of "
    f"{len(tickers)} companies**."
)
coverage_columns = st.columns(4)
for i, (metric_name, _, _, _) in enumerate(ranking_metrics):
    count = sum(metric_name in results.get(ticker, {}) for ticker in tickers)
    with coverage_columns[i % 4]:
        st.metric(metric_name, f"{count} / {len(tickers)}")
if companies_with_metrics == 0:
    st.error(
        "Yahoo Finance did not return usable metric values. Do not use these "
        "rankings for your assignment yet; check the data connection and retry."
    )
elif companies_with_metrics < len(tickers) * 0.5:
    st.warning(
        "Data coverage is low. Companies with missing metrics are not being "
        "treated as poor performers, but the rankings are incomplete."
    )


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
