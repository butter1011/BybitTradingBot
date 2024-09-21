Automated Trading Bot for Bybit Futures


This script implements an automated trading bot for Bybit Futures using the pybit library.
It places a limit sell order with stop loss and take profit levels, and monitors the market
for order execution and position management.

Key Features:
- Connects to Bybit Futures API (testnet)
- Places a limit sell order with specified trigger price
- Sets stop loss and take profit levels
- Monitors market price and open positions
- Handles order placement and position closure
- Implements error handling and logging

Configuration:
- SYMBOL: Trading pair (e.g., "BTCUSDT")
- TRIGGER_PRICE: Price at which to place the limit sell order
- STOP_LOSS_PRICE: Price at which to trigger the stop loss
- TAKE_PROFIT_PRICE: Price at which to take profit
- LEVERAGE: Trading leverage
- AMOUNT: Position size in terms of contracts or asset

Usage:
1. Set up API credentials (API_KEY and API_SECRET)
2. Configure trading parameters (SYMBOL, TRIGGER_PRICE, etc.)
3. Run the script to start the automated trading bot

Note: This script is for educational purposes only. Use at your own risk.

