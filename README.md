# SEC XBRL Ratio Engine - FastMCP Server

An Model Context Protocol (MCP) server enabling AI agents (Claude Desktop, Cursor, LangChain) to query audited, real-time SEC EDGAR XBRL financial ratios. Powered by the **x402 protocol** on Base Mainnet for autonomous micro-settlements.

## Features

- **9 TTM & MRQ Financial Ratios:** Calculates P/E, P/OCF, P/FCF, P/B, EV/EBITDA, ROIC %, Debt/Equity, Current Ratio, and Interest Coverage.
- **SEC EDGAR Audit Trails:** Includes accession numbers and filing dates for underlying US-GAAP XBRL tags.
- **x402 On-Chain Settlement:** Automatic $0.003 USDC micropayment authorization via Base Mainnet (`eip155:8453`) using Coinbase CDP.

## Available Tools

### `get_sec_financial_ratios`
Fetches and calculates TTM financial ratios for a given stock ticker and price.

* **Arguments:**
  * `ticker` (string, required): Stock ticker symbol (e.g., `NVDA`, `AAPL`, `MSFT`).
  * `price` (float, required): Current real-time stock price in USD (e.g., `120.50`).

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/mtbandy/sec-ratio-mcp.git](https://github.com/mtbandy/sec-ratio-mcp.git)
   cd sec-ratio-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory:
   ```env
   # Live x402 On-Chain Transactions (Requires ~0.003 USDC on Base)
   PAYMENT_PRIVATE_KEY=0x_your_evm_private_key
   ```

4. **Run in FastMCP Inspector:**
   ```bash
   fastmcp dev mcp_server.py
   ```

## Registry Integration

Integrate directly into Smithery.ai, Claude Desktop, or Cursor by registering this repository URL:

```text
[https://github.com/mtbandy/sec-ratio-mcp](https://github.com/mtbandy/sec-ratio-mcp)
```
