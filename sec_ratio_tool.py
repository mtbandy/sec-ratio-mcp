import os
import json
import base64
import time
import requests
from typing import Dict, Any
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "https://mtbandy--sec-ratio-engine-serve-app.modal.run"

def _execute_x402_paid_request(ticker: str, price: float) -> Dict[str, Any]:
    """Handles requesting the SEC engine via DEV_BYPASS_KEY or x402 signature."""
    dev_key = os.environ.get("DEV_BYPASS_KEY")
    ticker = ticker.upper()
    
    # 1. Dev Bypass Route (Fast, zero-latency testing)
    if dev_key:
        endpoint = f"{API_BASE_URL}/ratios?ticker={ticker}&price={price}&dev_key={dev_key}"
        res = requests.get(endpoint)
        res.raise_for_status()
        return res.json()
        
    endpoint = f"{API_BASE_URL}/ratios?ticker={ticker}&price={price}"
    
    # 2. Initial Request (Expect 402)
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    if response.status_code != 402:
        raise Exception(f"Unexpected status code {response.status_code}: {response.text}")
    
    # 3. Extract x402 Challenge
    payment_header = response.headers.get("PAYMENT-REQUIRED") or response.headers.get("X-PAYMENT-REQUIRED")
    if not payment_header:
        raise Exception("402 response missing PAYMENT-REQUIRED header.")
    
    challenge = json.loads(base64.b64decode(payment_header).decode("utf-8"))
    accept = challenge["accepts"][0]
    
    # 4. Sign Payment via EVM Private Key
    private_key = os.environ.get("PAYMENT_PRIVATE_KEY") or os.environ.get("ETH_PRIVATE_KEY")
    if not private_key:
        raise Exception(
            "Neither DEV_BYPASS_KEY nor PAYMENT_PRIVATE_KEY is set in environment. "
            "Set DEV_BYPASS_KEY for free dev mode, or PAYMENT_PRIVATE_KEY to sign x402 payments."
        )

    try:
        from eth_account import Account
        from eth_account.messages import encode_typed_data
    except ImportError:
        raise Exception("eth-account is required for x402 signatures. Run 'pip install eth-account'.")

    account = Account.from_key(private_key)
    
    current_time = int(time.time())
    valid_before = current_time + 3600
    nonce = "0x" + os.urandom(32).hex()

    # The payload strictly required by eth_account for hashing
    signing_message = {
        "from": account.address,
        "to": accept["payTo"],
        "value": int(accept["amount"]),
        "validAfter": 0,
        "validBefore": valid_before,
        "nonce": nonce
    }

    domain = {
        "name": accept.get("extra", {}).get("name", "USD Coin"),
        "version": accept.get("extra", {}).get("version", "2"),
        "chainId": 8453,
        "verifyingContract": accept["asset"]
    }
    
    types = {
        "TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"}
        ]
    }

    signable_message = encode_typed_data(domain_data=domain, message_types=types, message_data=signing_message)
    signed_msg = account.sign_message(signable_message)
    
    sig_hex = signed_msg.signature.hex()
    if not sig_hex.startswith("0x"):
        sig_hex = f"0x{sig_hex}"

    # The payload strictly required by CDP JSON schema validation (strings for uint256 fields)
    json_authorization = {
        "from": account.address,
        "to": accept["payTo"],
        "value": str(accept["amount"]),
        "validAfter": "0",
        "validBefore": str(valid_before),
        "nonce": nonce
    }

    payment_payload = {
        "x402Version": 2,
        "scheme": accept.get("scheme", "exact"),
        "network": accept.get("network", "eip155:8453"),
        "accepted": accept,
        "payload": {
            "authorization": json_authorization,
            "signature": sig_hex
        }
    }
    encoded_signature = base64.b64encode(json.dumps(payment_payload).encode("utf-8")).decode("utf-8")
    
    # 5. Retry with PAYMENT-SIGNATURE
    paid_response = requests.get(
        endpoint,
        headers={"PAYMENT-SIGNATURE": encoded_signature}
    )
    if paid_response.status_code != 200:
        raise Exception(f"Payment settlement failed ({paid_response.status_code}): {paid_response.text}")

    return paid_response.json()


@tool
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