import yfinance as yf
import pandas as pd


# Companies for our initial data test
TEST_COMPANIES = {
    "Enbridge": "ENB.TO",
    "Canadian National Railway": "CNR.TO",
    "Shopify": "SHOP.TO",
    "Canadian Tire": "CTC-A.TO",
    "Fortis": "FTS.TO",
}


def get_company_data(ticker_symbol):
    """
    Retrieve financial statements and company information
    from Yahoo Finance for one company.
    """
    try:
        company = yf.Ticker(ticker_symbol)

        return {
            "ticker": ticker_symbol,
            "info": company.get_info(),
            "income_statement": company.income_stmt,
            "balance_sheet": company.balance_sheet,
            "cash_flow": company.cashflow,
        }

    except Exception as error:
        return {
            "ticker": ticker_symbol,
            "error": str(error),
        }


def check_company_data(ticker_symbol):
    """
    Check which financial statements are available
    for a company.
    """
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return {
            "ticker": ticker_symbol,
            "status": "Download failed",
            "income_statement": False,
            "balance_sheet": False,
            "cash_flow": False,
        }

    income = data["income_statement"]
    balance = data["balance_sheet"]
    cash_flow = data["cash_flow"]

    return {
        "ticker": ticker_symbol,
        "status": "Retrieved",
        "income_statement": not income.empty,
        "balance_sheet": not balance.empty,
        "cash_flow": not cash_flow.empty,
    }


def test_company_universe():
    """
    Create a summary of statement availability
    for our five test companies.
    """
    results = []

    for company_name, ticker in TEST_COMPANIES.items():
        result = check_company_data(ticker)
        result["company"] = company_name
        results.append(result)

    return pd.DataFrame(results)

def inspect_company_fields(ticker_symbol):
    """
    List the financial fields available from Yahoo Finance
    for one company.
    """
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return {
            "ticker": ticker_symbol,
            "statement": "Download error",
            "field": data["error"],
        }

    results = []

    for statement_name in [
        "income_statement",
        "balance_sheet",
        "cash_flow",
    ]:
        statement = data[statement_name]

        for field in statement.index:
            results.append({
                "ticker": ticker_symbol,
                "statement": statement_name,
                "field": field,
            })

    return results

def check_metric_field_coverage(ticker_symbol):
    """
    Check whether key fields for our seven lecture metrics
    appear in Yahoo Finance financial statements.
    """
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return [{
            "ticker": ticker_symbol,
            "metric": "All metrics",
            "field": "Download error",
            "available": False,
        }]

    statements = {
        "income_statement": data["income_statement"],
        "balance_sheet": data["balance_sheet"],
        "cash_flow": data["cash_flow"],
    }

    # Fields to investigate. Yahoo Finance field names can vary.
    requirements = {
        "ROC": [
            ("income_statement", "EBIT"),
            ("balance_sheet", "Net PPE"),
            ("balance_sheet", "Current Assets"),
            ("balance_sheet", "Current Liabilities"),
        ],
        "Earnings Yield": [
            ("income_statement", "EBIT"),
            ("balance_sheet", "Cash And Cash Equivalents"),
            ("balance_sheet", "Current Assets"),
            ("balance_sheet", "Current Liabilities"),
            ("balance_sheet", "Total Debt"),
        ],
        "Book-to-Market": [
            ("balance_sheet", "Stockholders Equity"),
        ],
        "Gross Profit Metric": [
            ("income_statement", "Total Revenue"),
            ("income_statement", "Cost Of Revenue"),
            ("balance_sheet", "Total Assets"),
        ],
        "CFOA": [
            ("cash_flow", "Free Cash Flow"),
            ("balance_sheet", "Total Assets"),
        ],       
        "SNOA": [
            ("balance_sheet", "Total Assets"),
            ("balance_sheet", "Cash And Cash Equivalents"),
            ("balance_sheet", "Current Debt And Capital Lease Obligation"),
            ("balance_sheet", "Long Term Debt And Capital Lease Obligation"),
            ("balance_sheet", "Minority Interest"),
            ("balance_sheet", "Preferred Stock Equity"),
            ("balance_sheet", "Common Stock Equity"),
        ],
        "Altman Z-Score": [
            ("balance_sheet", "Working Capital"),
            ("balance_sheet", "Retained Earnings"),
            ("income_statement", "EBIT"),
            ("balance_sheet", "Stockholders Equity"),
            ("balance_sheet", "Total Liabilities Net Minority Interest"),
            ("income_statement", "Total Revenue"),
            ("balance_sheet", "Total Assets"),
        ],
    }

    results = []

    for metric, fields in requirements.items():
        for statement_name, field_name in fields:
            statement = statements[statement_name]
            available = field_name in statement.index

            results.append({
                "ticker": ticker_symbol,
                "metric": metric,
                "field": field_name,
                "statement": statement_name,
                "available": available,
            })

    return results

def inspect_snoa_inputs(ticker_symbol):
    """Inspect the balance-sheet values needed for SNOA."""
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return {"ticker": ticker_symbol, "error": data["error"]}

    balance = data["balance_sheet"]

    fields = [
        "Total Assets",
        "Cash And Cash Equivalents",
        "Current Debt And Capital Lease Obligation",
        "Long Term Debt And Capital Lease Obligation",
        "Minority Interest",
        "Preferred Stock Equity",
        "Common Stock Equity",
    ]

    results = []

    for field in fields:
       
        if field in balance.index:
            values = balance.loc[field].dropna()
            value = values.iloc[0] if not values.empty else None
            found = value is not None
        else:
            value = None
            found = False

        if field == "Preferred Stock Equity" and value is None:
            value = 0.0
            results.append({
                "ticker": ticker_symbol,
                "field": field,
                "latest_value": value,
                "field_found": False,
                "note": "Treated as zero per professor's instructions",
            })
        else:
            results.append({
                "ticker": ticker_symbol,
                "field": field,
                "latest_value": value,
                "field_found": found,
                "note": "",
            })


    return results

def get_snoa_equity_inputs(ticker_symbol):
    """
    Retrieve preferred stock and minority interest for SNOA.
    Uses zero for absent preferred stock, as instructed by the professor.
    Derives minority interest only when the available equity data
    supports that calculation.
    """
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return {
            "ticker": ticker_symbol,
            "minority_interest": None,
            "preferred_stock": None,
            "minority_interest_source": "Data retrieval failed",
            "preferred_stock_source": "Data retrieval failed",
        }

    balance = data["balance_sheet"]

    def latest_value(field):
        if field not in balance.index:
            return None

        values = balance.loc[field].dropna()

        if values.empty:
            return None

        return float(values.iloc[0])

    minority = latest_value("Minority Interest")
    preferred = latest_value("Preferred Stock Equity")

    minority_source = "Yahoo Finance: Minority Interest"
    preferred_source = "Yahoo Finance: Preferred Stock Equity"

    # If preferred stock is genuinely absent, use zero.
    if preferred is None:
        preferred = 0.0
        preferred_source = "Assumed zero: preferred stock field absent"

    # Derive minority interest only if equity components reconcile.
    if minority is None:
        gross_equity = latest_value("Total Equity Gross Minority Interest")
        common_equity = latest_value("Common Stock Equity")

        if gross_equity is not None and common_equity is not None:
            difference = gross_equity - common_equity

            # Only accept a non-negative difference.
            # Other equity components must be checked before relying on it.
            if difference >= 0 and preferred == 0:
                minority = difference
                minority_source = (
                    "Derived: Total Equity Gross Minority Interest "
                    "minus Common Stock Equity; verify reconciliation"
                )
            else:
                minority_source = "Could not safely derive minority interest"
        else:
            minority_source = "Minority interest unavailable"

    return {
        "ticker": ticker_symbol,
        "minority_interest": minority,
        "preferred_stock": preferred,
        "minority_interest_source": minority_source,
        "preferred_stock_source": preferred_source,
    }

def inspect_equity_reconciliation(ticker_symbol):
    """
    Compare Yahoo Finance equity fields to investigate
    whether minority interest can be derived reliably.
    """
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return {"ticker": ticker_symbol, "error": data["error"]}

    balance = data["balance_sheet"]

    fields = [
        "Total Equity Gross Minority Interest",
        "Common Stock Equity",
        "Preferred Stock Equity",
        "Minority Interest",
        "Stockholders Equity",
    ]

    results = []

    for field in fields:
        if field in balance.index:
            values = balance.loc[field].dropna()
            value = values.iloc[0] if not values.empty else None
        else:
            value = None

        results.append({
            "ticker": ticker_symbol,
            "field": field,
            "latest_value": value,
            "field_found": field in balance.index,
        })

    gross = next(
        (r["latest_value"] for r in results
         if r["field"] == "Total Equity Gross Minority Interest"),
        None,
    )
    common = next(
        (r["latest_value"] for r in results
         if r["field"] == "Common Stock Equity"),
        None,
    )

    results.append({
        "ticker": ticker_symbol,
        "field": "Gross equity minus common equity",
        "latest_value": (
            gross - common
            if gross is not None and common is not None
            else None
        ),
        "field_found": gross is not None and common is not None,
    })

    return results

def calculate_snoa(ticker_symbol):
    """
    Calculate SNOA using the professor's formula.

    SNOA = (Operating Assets - Operating Liabilities) / Total Assets

    Missing minority interest is not automatically treated as zero.
    Preferred stock is zero when absent, per the professor's instructions.
    """
    data = get_company_data(ticker_symbol)

    if "error" in data:
        return {
            "ticker": ticker_symbol,
            "snoa": None,
            "status": "Data retrieval failed",
            "details": data["error"],
        }

    balance = data["balance_sheet"]

    def latest_value(field):
        if field not in balance.index:
            return None

        values = balance.loc[field].dropna()

        if values.empty:
            return None

        return float(values.iloc[0])

    total_assets = latest_value("Total Assets")
    cash = latest_value("Cash And Cash Equivalents")
    short_term_debt = latest_value(
        "Current Debt And Capital Lease Obligation"
    )
    long_term_debt = latest_value(
        "Long Term Debt And Capital Lease Obligation"
    )
    minority_interest = latest_value("Minority Interest")
    preferred_stock = latest_value("Preferred Stock Equity")
    common_equity = latest_value("Common Stock Equity")

    # The professor says to use zero if preferred stock is absent.
    if preferred_stock is None:
        preferred_stock = 0.0

    # Stop if any required inputs are unavailable.
    required_inputs = {
        "Total Assets": total_assets,
        "Cash And Cash Equivalents": cash,
        "Current Debt And Capital Lease Obligation": short_term_debt,
        "Long Term Debt And Capital Lease Obligation": long_term_debt,
        "Minority Interest": minority_interest,
        "Common Stock Equity": common_equity,
    }

    missing = [
        name for name, value in required_inputs.items()
        if value is None
    ]

    if missing:
        return {
            "ticker": ticker_symbol,
            "snoa": None,
            "status": "Missing required data",
            "details": "Missing: " + ", ".join(missing),
        }

    if total_assets == 0:
        return {
            "ticker": ticker_symbol,
            "snoa": None,
            "status": "Invalid denominator",
            "details": "Total Assets is zero.",
        }

    operating_assets = total_assets - cash

    operating_liabilities = (
        total_assets
        - short_term_debt
        - long_term_debt
        - minority_interest
        - preferred_stock
        - common_equity
    )

    snoa = (
        operating_assets - operating_liabilities
    ) / total_assets

    return {
        "ticker": ticker_symbol,
        "total_assets": total_assets,
        "operating_assets": operating_assets,
        "operating_liabilities": operating_liabilities,
        "minority_interest": minority_interest,
        "preferred_stock": preferred_stock,
        "snoa": snoa,
        "status": "Calculated",
        "details": "Calculated using available reported inputs.",
    }

def calculate_book_to_market(ticker_symbol):
    """Calculate book-to-market using common equity / market cap."""

    try:
        company = yf.Ticker(ticker_symbol)
        info = company.get_info()
        balance_sheet = company.balance_sheet

        # Get the latest reported common stock equity.
        if (
            balance_sheet.empty
            or "Common Stock Equity" not in balance_sheet.index
        ):
            return {
                "ticker": ticker_symbol,
                "status": "Missing book value",
                "details": "Common Stock Equity is unavailable.",
            }

        equity_values = (
            balance_sheet.loc["Common Stock Equity"].dropna()
        )

        if equity_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing book value",
                "details": "No reported Common Stock Equity value.",
            }

        book_value = float(equity_values.iloc[0])

        # Get the company's market capitalization.
        market_cap = info.get("marketCap")

        if market_cap is None:
            return {
                "ticker": ticker_symbol,
                "book_value": book_value,
                "status": "Missing market cap",
                "details": "Yahoo Finance did not provide market cap.",
            }

        market_cap = float(market_cap)

        if market_cap <= 0:
            return {
                "ticker": ticker_symbol,
                "book_value": book_value,
                "market_cap": market_cap,
                "status": "Invalid market cap",
                "details": "Market cap must be greater than zero.",
            }

        # Professor's formula: Book Value / Market Capitalization.
        bm = book_value / market_cap

        return {
            "ticker": ticker_symbol,
            "book_value": book_value,
            "market_cap": market_cap,
            "book_to_market": bm,
            "status": "Calculated",
            "details": "Book value divided by market capitalization.",
        }

    except Exception as e:
        return {
            "ticker": ticker_symbol,
            "status": "Error",
            "details": str(e),
        }

def calculate_gross_profitability(ticker_symbol):
    """Calculate gross profitability using gross profit / total assets."""

    try:
        company = yf.Ticker(ticker_symbol)
        income_statement = company.income_stmt
        balance_sheet = company.balance_sheet

        # Get revenue.
        if income_statement.empty or "Total Revenue" not in income_statement.index:
            return {
                "ticker": ticker_symbol,
                "status": "Missing revenue",
                "details": "Total Revenue is unavailable.",
            }

        revenue_values = income_statement.loc["Total Revenue"].dropna()

        if revenue_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing revenue",
                "details": "No reported Total Revenue value.",
            }

        revenue = float(revenue_values.iloc[0])

        # Get cost of revenue (COGS).
        if "Cost Of Revenue" not in income_statement.index:
            return {
                "ticker": ticker_symbol,
                "status": "Missing COGS",
                "details": "Cost Of Revenue is unavailable.",
            }

        cogs_values = income_statement.loc["Cost Of Revenue"].dropna()

        if cogs_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing COGS",
                "details": "No reported Cost Of Revenue value.",
            }

        cogs = float(cogs_values.iloc[0])

        # Get total assets.
        if balance_sheet.empty or "Total Assets" not in balance_sheet.index:
            return {
                "ticker": ticker_symbol,
                "status": "Missing total assets",
                "details": "Total Assets is unavailable.",
            }

        asset_values = balance_sheet.loc["Total Assets"].dropna()

        if asset_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing total assets",
                "details": "No reported Total Assets value.",
            }

        total_assets = float(asset_values.iloc[0])

        if total_assets <= 0:
            return {
                "ticker": ticker_symbol,
                "status": "Invalid total assets",
                "details": "Total Assets must be greater than zero.",
            }

        # Professor's formula: (Revenue - COGS) / Total Assets.
        gross_profitability = (revenue - cogs) / total_assets

        return {
            "ticker": ticker_symbol,
            "revenue": revenue,
            "cogs": cogs,
            "total_assets": total_assets,
            "gross_profitability": gross_profitability,
            "status": "Calculated",
            "details": "Gross profit divided by total assets.",
        }

    except Exception as e:
        return {
            "ticker": ticker_symbol,
            "status": "Error",
            "details": str(e),
        }

def calculate_cfoa(ticker_symbol):
    """Calculate CFOA using four years of FCF / latest total assets."""

    try:
        company = yf.Ticker(ticker_symbol)
        cash_flow = company.cashflow
        balance_sheet = company.balance_sheet

        # Get annual free cash flow for four years.
        if cash_flow.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing cash flow",
                "details": "Yahoo Finance returned no cash flow statement.",
            }

        if "Free Cash Flow" not in cash_flow.index:
            return {
                "ticker": ticker_symbol,
                "status": "Missing FCF",
                "details": "Free Cash Flow is unavailable.",
            }

        fcf_values = cash_flow.loc["Free Cash Flow"].dropna()

        if len(fcf_values) < 4:
            return {
                "ticker": ticker_symbol,
                "status": "Insufficient FCF history",
                "details": (
                    f"Found {len(fcf_values)} annual FCF values; "
                    "four are required."
                ),
            }

        # Use the four most recent annual FCF values.
        four_year_fcf = fcf_values.iloc[:4].astype(float)
        total_fcf = float(four_year_fcf.sum())

        # Get the latest reported total assets.
        if (
            balance_sheet.empty
            or "Total Assets" not in balance_sheet.index
        ):
            return {
                "ticker": ticker_symbol,
                "status": "Missing total assets",
                "details": "Total Assets is unavailable.",
            }

        asset_values = balance_sheet.loc["Total Assets"].dropna()

        if asset_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing total assets",
                "details": "No reported Total Assets value.",
            }

        total_assets = float(asset_values.iloc[0])

        if total_assets <= 0:
            return {
                "ticker": ticker_symbol,
                "status": "Invalid total assets",
                "details": "Total Assets must be greater than zero.",
            }

        # Professor's formula: sum of four years of FCF / total assets.
        cfoa = total_fcf / total_assets

        return {
            "ticker": ticker_symbol,
            "fcf_years_used": len(four_year_fcf),
            "four_year_fcf_sum": total_fcf,
            "total_assets": total_assets,
            "cfoa": cfoa,
            "status": "Calculated",
            "details": "Four years of FCF divided by latest total assets.",
        }

    except Exception as e:
        return {
            "ticker": ticker_symbol,
            "status": "Error",
            "details": str(e),
        }

def calculate_roc(ticker_symbol):
    """Calculate ROC using EBIT / (Net PPE + Net Working Capital)."""

    try:
        company = yf.Ticker(ticker_symbol)
        income_statement = company.income_stmt
        balance_sheet = company.balance_sheet

        # Get the latest annual EBIT.
        if income_statement.empty or "EBIT" not in income_statement.index:
            return {
                "ticker": ticker_symbol,
                "status": "Missing EBIT",
                "details": "EBIT is unavailable.",
            }

        ebit_values = income_statement.loc["EBIT"].dropna()

        if ebit_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing EBIT",
                "details": "No reported EBIT value.",
            }

        ebit = float(ebit_values.iloc[0])

        # Check for required balance sheet data.
        required_rows = [
            "Net PPE",
            "Current Assets",
            "Current Liabilities",
        ]

        if balance_sheet.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet",
                "details": "Yahoo Finance returned no balance sheet.",
            }

        missing_rows = [
            row for row in required_rows
            if row not in balance_sheet.index
        ]

        if missing_rows:
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet data",
                "details": f"Missing fields: {', '.join(missing_rows)}",
            }

        # Use the latest reported annual balance sheet values.
        net_ppe_values = balance_sheet.loc["Net PPE"].dropna()
        current_assets_values = balance_sheet.loc["Current Assets"].dropna()
        current_liabilities_values = (
            balance_sheet.loc["Current Liabilities"].dropna()
        )

        if (
            net_ppe_values.empty
            or current_assets_values.empty
            or current_liabilities_values.empty
        ):
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet data",
                "details": "One or more required values are unavailable.",
            }

        net_ppe = float(net_ppe_values.iloc[0])
        current_assets = float(current_assets_values.iloc[0])
        current_liabilities = float(current_liabilities_values.iloc[0])

        working_capital = current_assets - current_liabilities
        capital = net_ppe + working_capital

        if capital == 0:
            return {
                "ticker": ticker_symbol,
                "status": "Invalid denominator",
                "details": "Net PPE + Net Working Capital equals zero.",
            }

        roc = ebit / capital

        return {
            "ticker": ticker_symbol,
            "ebit": ebit,
            "net_ppe": net_ppe,
            "net_working_capital": working_capital,
            "capital": capital,
            "roc": roc,
            "status": "Calculated",
            "details": "EBIT / (Net PPE + Net Working Capital).",
        }

    except Exception as e:
        return {
            "ticker": ticker_symbol,
            "status": "Error",
            "details": str(e),
        }

def calculate_ey(ticker_symbol):
    """Calculate Earnings Yield using EBIT / Total Enterprise Value."""

    try:
        company = yf.Ticker(ticker_symbol)
        info = company.get_info()
        income_statement = company.income_stmt
        balance_sheet = company.balance_sheet

        # Get the latest annual EBIT.
        if income_statement.empty or "EBIT" not in income_statement.index:
            return {
                "ticker": ticker_symbol,
                "status": "Missing EBIT",
                "details": "EBIT is unavailable.",
            }

        ebit_values = income_statement.loc["EBIT"].dropna()

        if ebit_values.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing EBIT",
                "details": "No reported EBIT value.",
            }

        ebit = float(ebit_values.iloc[0])

        # Get market capitalization.
        market_cap = info.get("marketCap")

        if market_cap is None or market_cap <= 0:
            return {
                "ticker": ticker_symbol,
                "status": "Missing market cap",
                "details": "Market capitalization is unavailable or invalid.",
            }

        # Check required balance sheet fields.
        required_rows = [
            "Cash Cash Equivalents And Short Term Investments",
            "Current Assets",
            "Current Liabilities",
            "Total Debt",
        ]

        if balance_sheet.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet",
                "details": "Yahoo Finance returned no balance sheet.",
            }

        missing_rows = [
            row for row in required_rows
            if row not in balance_sheet.index
        ]

        if missing_rows:
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet data",
                "details": f"Missing fields: {', '.join(missing_rows)}",
            }

        # Use the latest reported annual values.
        cash_values = (
            balance_sheet.loc[
                "Cash Cash Equivalents And Short Term Investments"
            ].dropna()
        )
        current_assets_values = balance_sheet.loc["Current Assets"].dropna()
        current_liabilities_values = (
            balance_sheet.loc["Current Liabilities"].dropna()
        )
        debt_values = balance_sheet.loc["Total Debt"].dropna()

        if any(
            values.empty
            for values in [
                cash_values,
                current_assets_values,
                current_liabilities_values,
                debt_values,
            ]
        ):
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet data",
                "details": "One or more required values are unavailable.",
            }

        cash = float(cash_values.iloc[0])
        current_assets = float(current_assets_values.iloc[0])
        current_liabilities = float(current_liabilities_values.iloc[0])
        total_debt = float(debt_values.iloc[0])

        # Preferred stock and minority interest default to zero only
        # when the corresponding balance sheet row is absent.
        preferred_stock = (
            float(balance_sheet.loc["Preferred Stock"].dropna().iloc[0])
            if "Preferred Stock" in balance_sheet.index
            and not balance_sheet.loc["Preferred Stock"].dropna().empty
            else 0.0
        )

        # Minority interest must be available or verified as zero.
        if (
            "Minority Interest" not in balance_sheet.index
            or balance_sheet.loc["Minority Interest"].dropna().empty
        ):
            return {
                "ticker": ticker_symbol,
                "status": "Missing minority interest",
                "details": (
                    "Yahoo Finance does not provide a standalone "
                    "Minority Interest value. Verify it before calculating EY."
                ),
            }

        minority_interest = float(
            balance_sheet.loc["Minority Interest"].dropna().iloc[0]
        )


        excess_cash = cash + current_assets - current_liabilities

        enterprise_value = (
            float(market_cap)
            + total_debt
            - excess_cash
            + preferred_stock
            + minority_interest
        )

        if enterprise_value <= 0:
            return {
                "ticker": ticker_symbol,
                "status": "Invalid enterprise value",
                "details": "Total Enterprise Value must be positive.",
            }

        ey = ebit / enterprise_value

        return {
            "ticker": ticker_symbol,
            "ebit": ebit,
            "market_cap": float(market_cap),
            "total_debt": total_debt,
            "excess_cash": excess_cash,
            "preferred_stock": preferred_stock,
            "minority_interest": minority_interest,
            "enterprise_value": enterprise_value,
            "ey": ey,
            "status": "Calculated",
            "details": "EBIT / Total Enterprise Value.",
        }

    except Exception as e:
        return {
            "ticker": ticker_symbol,
            "status": "Error",
            "details": str(e),
        }

def calculate_altman_z(ticker_symbol):
    """Calculate Altman Z-score using the professor's specified formula."""

    try:
        company = yf.Ticker(ticker_symbol)
        info = company.get_info()
        income_statement = company.income_stmt
        balance_sheet = company.balance_sheet

        # Required annual income statement and balance sheet fields.
        required_balance_rows = [
            "Current Assets",
            "Current Liabilities",
            "Total Assets",
            "Retained Earnings",
            "Total Liabilities Net Minority Interest",
        ]

        if balance_sheet.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet",
                "details": "Yahoo Finance returned no balance sheet.",
            }

        missing_rows = [
            row for row in required_balance_rows
            if row not in balance_sheet.index
        ]

        if missing_rows:
            return {
                "ticker": ticker_symbol,
                "status": "Missing balance sheet data",
                "details": f"Missing fields: {', '.join(missing_rows)}",
            }

        if income_statement.empty:
            return {
                "ticker": ticker_symbol,
                "status": "Missing income statement",
                "details": "Yahoo Finance returned no income statement.",
            }

        required_income_rows = ["EBIT", "Total Revenue"]

        missing_income_rows = [
            row for row in required_income_rows
            if row not in income_statement.index
        ]

        if missing_income_rows:
            return {
                "ticker": ticker_symbol,
                "status": "Missing income statement data",
                "details": (
                    f"Missing fields: {', '.join(missing_income_rows)}"
                ),
            }

        # Retrieve the latest reported annual values.
        def latest_value(statement, row):
            values = statement.loc[row].dropna()
            if values.empty:
                return None
            return float(values.iloc[0])

        current_assets = latest_value(balance_sheet, "Current Assets")
        current_liabilities = latest_value(
            balance_sheet, "Current Liabilities"
        )
        total_assets = latest_value(balance_sheet, "Total Assets")
        retained_earnings = latest_value(balance_sheet, "Retained Earnings")
        total_liabilities = latest_value(
            balance_sheet, "Total Liabilities Net Minority Interest"
        )
        ebit = latest_value(income_statement, "EBIT")
        sales = latest_value(income_statement, "Total Revenue")

        required_values = {
            "Current Assets": current_assets,
            "Current Liabilities": current_liabilities,
            "Total Assets": total_assets,
            "Retained Earnings": retained_earnings,
            "Total Liabilities": total_liabilities,
            "EBIT": ebit,
            "Sales": sales,
        }

        missing_values = [
            name for name, value in required_values.items()
            if value is None
        ]

        if missing_values:
            return {
                "ticker": ticker_symbol,
                "status": "Missing financial values",
                "details": (
                    f"No reported value for: {', '.join(missing_values)}"
                ),
            }


        # Market value of equity is represented by market capitalization.
        market_cap = info.get("marketCap")

        if market_cap is None or market_cap <= 0:
            try:
                market_cap = company.fast_info.get("market_cap")
            except Exception:
                market_cap = None

        if market_cap is None or market_cap <= 0:
            return {
                "ticker": ticker_symbol,
                "status": "Missing market cap",
                "details": "Market capitalization is unavailable or invalid.",
            }

        if total_assets <= 0 or total_liabilities <= 0:
            return {
                "ticker": ticker_symbol,
                "status": "Invalid denominator",
                "details": "Total assets and liabilities must be positive.",
            }

        working_capital = current_assets - current_liabilities

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = float(market_cap) / total_liabilities
        x5 = sales / total_assets

        z_score = (
            0.012 * x1
            + 0.014 * x2
            + 0.033 * x3
            + 0.006 * x4
            + 0.999 * x5
        )

        return {
            "ticker": ticker_symbol,
            "working_capital": working_capital,
            "total_assets": total_assets,
            "retained_earnings": retained_earnings,
            "ebit": ebit,
            "market_cap": float(market_cap),
            "total_liabilities": total_liabilities,
            "sales": sales,
            "x1": x1,
            "x2": x2,
            "x3": x3,
            "x4": x4,
            "x5": x5,
            "altman_z": z_score,
            "status": "Calculated",
            "details": "Calculated using the professor's specified formula.",
        }

    except Exception as e:
        return {
            "ticker": ticker_symbol,
            "status": "Error",
            "details": str(e),
        }
