"""
Build a 1,000-company stock universe CSV from current U.S. exchange directories
plus the app's 15 Canadian test companies.

Run:
    python build_company_universe.py

Output:
    company_universe.csv

The U.S. listings come from Nasdaq Trader's public symbol directories.
This excludes test issues, ETFs, and obvious non-common-stock security types.
Review the output before using it for financial analysis.
"""
from io import StringIO
from pathlib import Path
import pandas as pd

OUT = Path("company_universe.csv")

CANADIAN = [
    ("SHOP.TO", "Shopify Inc.", "TSX", "Canada"),
    ("CTC-A.TO", "Canadian Tire Corporation Limited", "TSX", "Canada"),
    ("CNR.TO", "Canadian National Railway Company", "TSX", "Canada"),
    ("ENB.TO", "Enbridge Inc.", "TSX", "Canada"),
    ("FTS.TO", "Fortis Inc.", "TSX", "Canada"),
    ("CP.TO", "Canadian Pacific Kansas City Limited", "TSX", "Canada"),
    ("CNQ.TO", "Canadian Natural Resources Limited", "TSX", "Canada"),
    ("SU.TO", "Suncor Energy Inc.", "TSX", "Canada"),
    ("ATD.TO", "Alimentation Couche-Tard Inc.", "TSX", "Canada"),
    ("DOL.TO", "Dollarama Inc.", "TSX", "Canada"),
    ("MG.TO", "Magna International Inc.", "TSX", "Canada"),
    ("TRI.TO", "Thomson Reuters Corporation", "TSX", "Canada"),
    ("WCN.TO", "Waste Connections Inc.", "TSX", "Canada"),
    ("BCE.TO", "BCE Inc.", "TSX", "Canada"),
    ("CU.TO", "Canadian Utilities Limited", "TSX", "Canada"),
]

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

EXCLUDE_TERMS = (
    " ETF", " FUND", " WARRANT", " PREFERRED", " DEPOSITARY",
    " DEBENTURE", " NOTE", " UNITS", " RIGHT", " RIGHTS",
    " ETN", " INDEX", " TRUST PREFERRED", " SUBORDINATED"
)

def read_pipe_file(url):
    df = pd.read_csv(url, sep="|", dtype=str)
    # Nasdaq directory has a final timestamp row; keep rows with a symbol.
    return df[df.iloc[:, 0].notna() & ~df.iloc[:, 0].astype(str).str.startswith("File Creation Time")].copy()

def main():
    nasdaq = read_pipe_file(NASDAQ_URL)
    other = read_pipe_file(OTHER_URL)

    # Nasdaq-listed securities
    nasdaq = nasdaq[
        (nasdaq.get("Test Issue", "N") == "N")
        & (nasdaq.get("ETF", "N") == "N")
    ].copy()
    n = pd.DataFrame({
        "ticker": nasdaq["Symbol"].astype(str),
        "company_name": nasdaq["Security Name"].astype(str),
        "exchange": "NASDAQ",
        "country": "United States",
    })

    # Other exchange-listed securities: N=NYSE, A=NYSE American, P=NYSE Arca, etc.
    other = other[
        (other.get("Test Issue", "N") == "N")
        & (other.get("ETF", "N") == "N")
    ].copy()
    exchange_names = {"N": "NYSE", "A": "NYSE American", "P": "NYSE Arca", "Z": "Cboe", "V": "IEX"}
    o = pd.DataFrame({
        "ticker": other["ACT Symbol"].astype(str),
        "company_name": other["Security Name"].astype(str),
        "exchange": other["Exchange"].map(exchange_names).fillna("U.S. exchange"),
        "country": "United States",
    })

    us = pd.concat([n, o], ignore_index=True)
    us["ticker"] = us["ticker"].str.strip()
    us["company_name"] = us["company_name"].str.strip()
    us = us[us["ticker"].str.match(r"^[A-Z][A-Z0-9.-]{0,5}$", na=False)]
    upper_names = us["company_name"].str.upper()
    us = us[~upper_names.apply(lambda name: any(term in name for term in EXCLUDE_TERMS))]
    us = us.drop_duplicates(subset="ticker").sort_values(["exchange", "ticker"])

    # Keep 985 U.S. listings plus the 15 Canadian seed companies = 1,000 rows.
    us = us.head(985)
    ca = pd.DataFrame(CANADIAN, columns=["ticker", "company_name", "exchange", "country"])
    result = pd.concat([ca, us], ignore_index=True).drop_duplicates(subset="ticker")
    result.to_csv(OUT, index=False)
    print(f"Created {OUT.resolve()} with {len(result)} companies.")
    print("Columns: ticker, company_name, exchange, country")
    print("Note: verify ticker eligibility and financial-statement coverage before ranking.")

if __name__ == "__main__":
    main()
