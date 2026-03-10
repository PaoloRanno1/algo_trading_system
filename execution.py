import os
from typing import Dict, Any
from dotenv import load_dotenv

# Optional Alpaca-Py setup (if keys aren't provided, we'll mock it)
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    HAS_ALPACA = True
except ImportError:
    HAS_ALPACA = False
    print("WARNING: alpaca-py not installed properly. Using mock execution.")

load_dotenv()

# Constants
MOCK_PORTFOLIO_VALUE = 10000.0  # $10,000 dummy portfolio
MAX_ASSET_WEIGHT_LIMIT = 0.50   # 50% risk limit per asset

def enforce_risk_limits(target_allocations) -> Dict[str, float]:
    """
    Applies the 50% max risk threshold for any single asset.
    Handles both Dict and List formats from the LLM.
    """
    adjusted_allocations = {}
    
    # Handle the new Multi-Agent List of Dicts format
    if isinstance(target_allocations, list):
        for item in target_allocations:
            ticker = item.get("ticker", "UNKNOWN")
            weight = item.get("weight", 0.0)
            if weight > MAX_ASSET_WEIGHT_LIMIT:
                print(f"RISK LIMIT EXCEEDED: {ticker} target is {weight*100}%. Capping at {MAX_ASSET_WEIGHT_LIMIT*100}%.")
                adjusted_allocations[ticker] = MAX_ASSET_WEIGHT_LIMIT
            else:
                adjusted_allocations[ticker] = weight
    # Backwards compatibility for the old Dict format
    elif isinstance(target_allocations, dict):
        for ticker, weight in target_allocations.items():
            if weight > MAX_ASSET_WEIGHT_LIMIT:
                print(f"RISK LIMIT EXCEEDED: {ticker} target is {weight*100}%. Capping at {MAX_ASSET_WEIGHT_LIMIT*100}%.")
                adjusted_allocations[ticker] = MAX_ASSET_WEIGHT_LIMIT
            else:
                adjusted_allocations[ticker] = weight
            
    return adjusted_allocations

def calculate_target_values(portfolio_value: float, target_weights: Dict[str, float]) -> Dict[str, float]:
    """
    Converts percent allocations into absolute dollar values based on total portfolio value.
    """
    target_values = {}
    for ticker, weight in target_weights.items():
        if ticker.upper() != "CASH":
            target_values[ticker.upper()] = portfolio_value * weight
    return target_values

def execute_trades(allocation_plan: Dict[str, Any], live: bool = False):
    """
    Phase 3: Execution Layer
    Takes the structured LLM output (allocation_plan) and calculates/executes trades.
    """
    print("\n=========================================")
    print("      PHASE 3: TRADE EXECUTION")
    print("=========================================\n")
    
    if not allocation_plan or "target_allocations" not in allocation_plan:
        print("Error: Invalid allocation plan received.")
        return

    print(f"Current Macro Regime Identified: {allocation_plan.get('macro_regime_identified', 'Unknown')}")
    if "reasoning_steps" in allocation_plan:
        print(f"\nCommander Agent Reasoning:\n{allocation_plan['reasoning_steps']}\n")
    
    print(f"Portfolio Value: ${MOCK_PORTFOLIO_VALUE:,.2f}")
    
    # 1. Enforce Risk Constraints
    raw_allocations = allocation_plan["target_allocations"]
    safe_allocations = enforce_risk_limits(raw_allocations)
    
    # 2. Calculate Dollar Values
    target_positions = calculate_target_values(MOCK_PORTFOLIO_VALUE, safe_allocations)
    
    print("\n--- Target Portfolio Dollar Allocations ---")
    for ticker, dollar_value in target_positions.items():
        print(f"  {ticker}: ${dollar_value:,.2f}")
        
    # 3. Connect to Alpaca / Mock Execution
    api_key = os.environ.get("ALPACA_API_KEY")
    api_secret = os.environ.get("ALPACA_SECRET_KEY")
    
    if live and HAS_ALPACA and api_key and api_secret:
        print("\nConnecting to Alpaca Market API for LIVE Execution (Paper)...")
        trading_client = TradingClient(api_key, api_secret, paper=True)
        
        try:
            account = trading_client.get_account()
            if account.trading_blocked:
                print("Trading is currently blocked on this Alpaca account.")
                return
            
            # Since this is a demo, we'll execute buys directly for the target notional value.
            # In a real system, you would first calculate deltas between *current* portfolio 
            # and *target* portfolio to generate buy/sell orders.
            
            for ticker, notional_value in target_positions.items():
                if notional_value > 0:
                    print(f"SUBMITTING ORDER: Buy ${notional_value:.2f} of {ticker}")
                    market_order_data = MarketOrderRequest(
                        symbol=ticker,
                        notional=notional_value,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY
                    )
                    order = trading_client.submit_order(order_data=market_order_data)
                    print(f"Order submitted successfully ({order.id})")
                    
        except Exception as e:
            print(f"Alpaca API Error: {e}")
            
    else:
        print("\nMock Execution Mode (No live API keys detected or live=False)")
        print("The following mock orders would be sent:")
        for ticker, notional_value in target_positions.items():
            if notional_value > 0:
                print(f"  MOCK ORDER: Market Buy ${notional_value:,.2f} of {ticker}")
                
    print("\n=========================================")
    print("      EXECUTION PHASE COMPLETE")
    print("=========================================\n")


if __name__ == "__main__":
    # Mock data to test execution.py independently
    mock_allocation = {
        "macro_regime_identified": "Crypto-Led Risk-On Expansion",
        "confidence_score": 0.85,
        "target_allocations": {
            "IBIT": 0.60, # Deliberately > 50% to trigger risk constraints
            "USO": 0.10,
            "SPY": 0.20,
            "CASH": 0.10
        }
    }
    execute_trades(mock_allocation, live=False)
