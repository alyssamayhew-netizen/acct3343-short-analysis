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
            ("balance_sheet", "Current Debt"),
            ("balance_sheet", "Long Term Debt"),
            ("balance_sheet", "Minority Interest"),
            ("balance_sheet", "Preferred Stock"),
            ("balance_sheet", "Stockholders Equity"),
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
