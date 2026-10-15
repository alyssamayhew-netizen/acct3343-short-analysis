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
            value = balance.loc[field].iloc[0]
            results.append({
                "ticker": ticker_symbol,
                "field": field,
                "latest_value": value,
                "field_found": True,
            })
        else:
            results.append({
                "ticker": ticker_symbol,
                "field": field,
                "latest_value": None,
                "field_found": False,
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
