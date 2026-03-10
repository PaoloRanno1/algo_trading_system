# AI Quantitative Algorithmic Trading System

A modular, cross-asset algorithmic trading pipeline that harnesses both traditional financial data and prediction market probabilities (via Polymarket) to inform macro-regime modeling and generate automated portfolio allocations using a Large Language Model (Google Gemini).

## Overview

The system is split into three main operational phases built entirely in Python:

1. **Phase 1: Data Ingestion (`data_fetcher.py`)** 
   - Connects to the Polymarket CLOB (Central Limit Order Book) API to retrieve real-time implied probabilities of real-world macro events (e.g., "Will Bitcoin reach $100k?").
   - Pulls traditional ETF market data simultaneously via `yfinance`.
   
2. **Phase 2: LLM Synthesis Layer (`llm_brain.py`)**
   - Feeds the aggregated quantitative data directly into Google Gemini 2.5 Pro.
   - Using a strict quantitative persona prompt, the LLM analyzes the data, declares a macro-economic regime, provides a confidence score, and outputs optimal portfolio weights for a specific basket of ETFs (`IBIT`, `USO`, `SPY`, `CASH`) via strict structured JSON generation.
   
3. **Phase 3: Execution Layer (`execution.py`)**
   - Parses the target allocation JSON.
   - Translates desired percentages into absolute dollar amounts scaled against a hypothetical $10,000 Portfolio. 
   - Automatically enforces a **50% maximum risk guardrail**: if the LLM attempts to over-allocate to a single risky asset (e.g., 60% IBIT), the system automatically clips it at 50% to ensure sensible portfolio diversification.
   - Simulates (or executes live) the required Market Buys through the `alpaca-py` API.

## Project Structure

- `demo.ipynb`: An interactive Jupyter Notebook demonstrating all three phases connected seamlessly end-to-end.
- `data_fetcher.py`: Handles async web requests to Polymarket and Yahoo Finance.
- `llm_brain.py`: Manages the Gemini API connection, Pydantic strict structure mapping, and prompting architecture.
- `execution.py`: Calculates portfolio sizing, enforces risk constraints, and handles Alpaca exchange routing.
- `requirements.txt`: Master project dependencies.
- `.env`: API Key storage.

## Requirements & Setup

This project uses Python 3.13+ and a virtual environment. 

1. Create and activate a `.venv`:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. Install the necessary libraries via pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **API Keys**:
   Create a `.env` file in the root directory and supply your keys:
   ```env
   GEMINI_API_KEY="your_google_genai_key"
   
   # Optional (for live Paper Trading via Alpaca)
   ALPACA_API_KEY="your_alpaca_key"
   ALPACA_SECRET_KEY="your_alpaca_secret"
   ```

## Usage

To quickly test the entire system's logic flow, you can run the Jupyter Notebook provided:
1. Make sure `ipykernel` is installed in your virtual environment.
2. Open `demo.ipynb`.
3. Select your `.venv` environment or the registered `algo_trading_system` kernel.
4. "Run All Cells" to see Data Ingestion -> LLM Sizing -> Alpaca Mock Execution.

Alternatively, the components can be executed independently from the command line:

```bash
python data_fetcher.py
python llm_brain.py
python execution.py
```

## Security & Risk Warning
This is an experimental proof-of-concept pipeline intended for educational and algorithmic research purposes only. The LLM synthesis layer may occasionally "hallucinate" market rationale. Always use Mock / Paper Trading credentials with external API brokers to avoid real financial risk.
