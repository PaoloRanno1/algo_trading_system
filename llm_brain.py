import os
import json
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from data_fetcher import fetch_traditional_data, fetch_polymarket_event

# Load environment variables from .env file if it exists
load_dotenv()

# Initialize the Gemini client
client = genai.Client()

# ---------------------------------------------------------
# PYDANTIC SCHEMAS FOR STRUCTURED LLM OUTPUTS
# ---------------------------------------------------------

class TickerList(BaseModel):
    tickers: list[str] = Field(description="A list of 4 to 6 traditional finance ticker symbols (e.g. ['SPY', 'GLD', 'USO', 'IBIT', 'TLT']) highly correlated to the event.")

class AssetAllocation(BaseModel):
    ticker: str = Field(description="The ticker symbol")
    weight: float = Field(description="The target portfolio weighting (e.g. 0.25 for 25%).")

class AllocationPlan(BaseModel):
    reasoning_steps: str = Field(description="A detailed paragraph explaining WHY the specific tickers and weights were chosen, synthesizing the debate between the Alpha and Risk agents.")
    macro_regime_identified: str = Field(description="A descriptive string of the current market regime.")
    confidence_score: float = Field(description="A float between 0.0 and 1.0 representing confidence.")
    target_allocations: list[AssetAllocation] = Field(description="Target portfolio weightings. The weights MUST sum to exactly 1.0.")

# ---------------------------------------------------------
# AGENT PROMPTS & LOGIC
# ---------------------------------------------------------

def run_agent(model_name: str, system_prompt: str, user_prompt: str, response_schema: type[BaseModel] = None) -> Any:
    """Helper to run a Gemini agent. Optionally enforces a JSON schema."""
    try:
        if response_schema:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.2, 
            )
        else:
            config = types.GenerateContentConfig(temperature=0.4)
            
        response = client.models.generate_content(
            model=model_name,
            contents=[system_prompt, user_prompt],
            config=config,
        )
        
        if response_schema and response.text:
            return json.loads(response.text)
        return response.text
    except Exception as e:
        print(f"Error executing agent: {e}")
        return None

def research_agent(event_data: Dict[str, Any]) -> List[str]:
    """Agent 1: Determines which assets to trade based on the event."""
    sys_prompt = "You are an expert quantitative researcher. Given a geopolitical or macroeconomic event, output EXACTLY 4 to 6 highly liquid traditional finance tickers (ETFs or major stocks) that would be most heavily impacted by the event. Always include 'CASH' or a treasury ETF like 'SHV' or 'TLT' as a defensive option."
    
    user_prompt = f"Event Title: {event_data['title']}\nImplied Probability: {event_data['implied_probability']}"
    print("[Agent 1] Research: Selecting optimal tickers...")
    
    result = run_agent('gemini-2.5-flash', sys_prompt, user_prompt, response_schema=TickerList)
    if result and 'tickers' in result:
        # Guarantee CASH is available for safety
        tickers = result['tickers']
        if "CASH" not in tickers:
            tickers.append("CASH")
        return tickers
    return ["SPY", "GLD", "USO", "IBIT", "CASH"] # Fallback

def alpha_quant_agent(event_data: Dict[str, Any], market_data: str) -> str:
    """Agent 2: Proposes an aggressive speculative portfolio strategy."""
    sys_prompt = "You are the 'Alpha Quant' of a hedge fund. You are highly aggressive, seeking maximum upside and alpha generation. Given the Polymarket odds and current ticker prices, write a 1-paragraph strategy proposing an aggressive, risk-on allocation structure."
    user_prompt = f"Event: {event_data['title']}\nOdds: {event_data['implied_probability']}\nMarket Prices:\n{market_data}"
    print("[Agent 2] Alpha Quant: Drafting aggressive proposal...")
    return run_agent('gemini-2.5-pro', sys_prompt, user_prompt)

def risk_manager_agent(event_data: Dict[str, Any], market_data: str, alpha_proposal: str) -> str:
    """Agent 3: Proposes a conservative, defensive strategy to counter the Alpha Quant."""
    sys_prompt = "You are the 'Chief Risk Officer' of a hedge fund. You are highly conservative, seeking capital preservation, hedging, and minimal drawdown. Read the Alpha Quant's aggressive proposal and write a 1-paragraph counter-strategy that heavily focuses on defensive assets and CASH."
    user_prompt = f"Event: {event_data['title']}\nOdds: {event_data['implied_probability']}\nMarket Prices:\n{market_data}\n\nAlpha Quant Proposal to Critique:\n{alpha_proposal}"
    print("[Agent 3] Risk Manager: Drafting defensive counter-proposal...")
    return run_agent('gemini-2.5-pro', sys_prompt, user_prompt)

def commander_agent(event_data: Dict[str, Any], market_data: str, alpha_proposal: str, risk_proposal: str) -> Dict[str, Any]:
    """Agent 4: Synthesizes the debate into final structured JSON allocations."""
    sys_prompt = """You are the 'Portfolio Commander'. You synthesize macro data, Aggressive Alpha Strategies, and Conservative Risk Strategies to determine the ultimate capital allocation.
    
    RULES:
    1. Your output MUST be strict JSON conforming to the AllocationPlan schema.
    2. The target_allocations weights MUST sum exactly to 1.0.
    3. Your reasoning_steps must explicitly mention resolving the tension between the Alpha and Risk proposals."""
    
    user_prompt = f"Event: {event_data['title']} ({event_data['implied_probability']} odds)\nMarket Data: {market_data}\n\nAlpha Proposal: {alpha_proposal}\n\nRisk Proposal: {risk_proposal}"
    print("[Agent 4] Commander: Synthesizing debate and generating final allocation plan...")
    return run_agent('gemini-2.5-pro', sys_prompt, user_prompt, response_schema=AllocationPlan)

# ---------------------------------------------------------
# MAIN ORCHESTRATOR
# ---------------------------------------------------------

async def analyze_market_event_multi_agent(polymarket_slug: str) -> Optional[Dict[str, Any]]:
    """
    Orchestrates the entire Multi-Agent Debate pipeline given a Polymarket slug.
    """
    # 1. Fetch Event Base Data
    print(f"Fetching base data for Polymarket Slug: {polymarket_slug}")
    event_data = await fetch_polymarket_event(polymarket_slug)
    
    # 2. Agent 1: Research Agent (Ticker Selection)
    tickers = research_agent(event_data)
    print(f"   -> Selected Tickers: {tickers}")
    
    # 3. Fetch Pricing for Selected Tickers
    print("Fetching live market prices for selected tickers...")
    traditional_data = await fetch_traditional_data(tickers)
    market_data_str = json.dumps(traditional_data, indent=2)
    
    # 4. Agent 2: Alpha Quant Proposal
    alpha_proposal = alpha_quant_agent(event_data, market_data_str)
    
    # 5. Agent 3: Risk Manager Counter-Proposal
    risk_proposal = risk_manager_agent(event_data, market_data_str, alpha_proposal)
    
    # 6. Agent 4: Commander Synthesis (Final JSON)
    final_plan = commander_agent(event_data, market_data_str, alpha_proposal, risk_proposal)
    
    return final_plan

if __name__ == "__main__":
    import asyncio
    async def main():
        result = await analyze_market_event_multi_agent("bitcoin-to-100k-in-2024")
        print("\n--- Final Output ---")
        print(json.dumps(result, indent=2))
        
    asyncio.run(main())
