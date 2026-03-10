import asyncio
import aiohttp
import yfinance as yf
from typing import Dict, Any, List

async def fetch_polymarket_event(market_slug: str) -> Dict[str, Any]:
    """
    Fetches the Polymarket event title, description, and implied probability.
    """
    # Gamma API endpoint for events
    url = f"https://gamma-api.polymarket.com/events?slug={market_slug}"
    
    result = {
        "slug": market_slug,
        "title": "Unknown Event",
        "implied_probability": 0.0
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data and len(data) > 0:
                    event = data[0]
                    result["title"] = event.get('title', 'Unknown Event')
                    
                    markets = event.get('markets', [])
                    if markets:
                        # outcomePrices array typically aligns with the condition tokens (e.g., 'Yes', 'No')
                        outcome_prices = markets[0].get('outcomePrices', ['0', '0'])
                        try:
                            # Index 0 is typically the 'Yes' probability
                            result["implied_probability"] = float(outcome_prices[0])
                        except (IndexError, ValueError):
                            pass
    return result

async def fetch_traditional_data(tickers: List[str]) -> Dict[str, float]:
    """
    Fetches the current price of multiple traditional tickers using yfinance.
    """
    def get_prices():
        prices = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                try:
                    prices[ticker] = stock.fast_info.last_price
                except AttributeError:
                    prices[ticker] = stock.info.get('regularMarketPrice', 0.0)
            except Exception:
                prices[ticker] = 0.0
        return prices
            
    return await asyncio.to_thread(get_prices)

if __name__ == "__main__":
    async def main():
        event = await fetch_polymarket_event("bitcoin-to-100k-in-2024")
        print(f"Event: {event['title']} | Prob: {event['implied_probability']}")
        
        prices = await fetch_traditional_data(["IBIT", "SPY"])
        print(f"Prices: {prices}")

    asyncio.run(main())
