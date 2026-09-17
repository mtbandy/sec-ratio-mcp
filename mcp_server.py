import json
from dotenv import load_dotenv
from fastmcp import FastMCP
from sec_ratio_tool import _execute_x402_paid_request

load_dotenv()

mcp = FastMCP("SEC XBRL Ratio Engine")

@mcp.tool()
def get_sec_financial_ratios(ticker: str, price: float) -> str:
    """Calculates 9 TTM financial ratios (P/E, P/OCF, P/FCF, P/B, EV/EBITDA, ROIC %, 
    Debt/Equity, Current Ratio, Interest Coverage) directly from official SEC EDGAR XBRL filings 
    with accession audit trails. 

    Disclosures: Financial institutions and IFRS ADRs return null for unclassified 
    balance sheet structures or missing US-GAAP taxonomy tags.
    
    Args:
        ticker: Stock ticker symbol (e.g. 'NVDA', 'AAPL', 'MSFT').
        price: Current real-time stock price in USD as a float (e.g. 120.50).
    """
    try:
        data = _execute_x402_paid_request(ticker, price)
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error executing SEC ratio query: {str(e)}"

if __name__ == "__main__":
    mcp.run()