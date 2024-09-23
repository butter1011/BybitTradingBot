
# Import necessary libraries
import time
import logging
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any

# Configure logging settings
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# API credentials (Note: It's better to use environment variables for sensitive information)
API_KEY = 'r20vk2T6FIl5BhVgg4'
API_SECRET = 'sRL0lTzifGRIlMhHZIBCEs5RbQbeeUz4DD2R'

class TradingBot:
    def __init__(self):
        # Initialize the HTTP session for API communication
        self.session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
        
        # Set trading parameters
        self.symbol = 'BTCUSDT'
        self.trigger_price = Decimal(input("Enter the trigger price: "))
        self.order_price = Decimal(input("Enter the order price: "))
        self.stop_loss_price = self.get_stop_loss_price()
        self.amount = Decimal(input("Enter the amount: "))
        self.leverage = int(input("Enter the leverage: "))

    def get_stop_loss_price(self) -> Decimal:
        # Get stop loss price from user or use default
        user_input = input("Enter the stop loss price (press Enter for default): ")
        if user_input:
            return Decimal(user_input)
        else:
            return self.trigger_price + Decimal('1')

    def get_market_price(self) -> Optional[Decimal]:
        # Fetch current market price
        try:
            ticker = self.session.get_tickers(category="linear", symbol=self.symbol)
            return Decimal(ticker["result"]["list"][0]["lastPrice"])
        except Exception as e:
            logger.error(f"Error getting market price: {e}\n")
            return None

    def get_open_order(self) -> Optional[Dict[str, Any]]:
        # Check for open sell limit orders
        try:
            orders = self.session.get_open_orders(category="linear", symbol=self.symbol)
            for order in orders["result"]["list"]:
                if order["orderType"] == "Limit" and order["side"] == "Sell":
                    logger.info(f"Found open order: {order['orderStatus']}")
                    return order
            return None
        except Exception as e:
            logger.error(f"Error checking open orders: {e}\n")
            return None

    def get_order_history(self) -> Optional[list[Dict[str, Any]]]:
        # Fetch recent order history
        try:
            order_history = self.session.get_order_history(category="linear", symbol=self.symbol, limit=1)
            return order_history["result"]["list"]
        except Exception as e:
            logger.error(f"Error checking order history: {e}\n")
            return None

    def get_open_position(self) -> Optional[Dict[str, Any]]:
        # Check for open positions with stop loss
        try:
            positions = self.session.get_positions(category="linear", symbol=self.symbol)
            for pos in positions["result"]["list"]:
                if pos["stopLoss"] != "":
                    logger.info(f"Found position... {pos['curRealisedPnl']}")
                    return pos
            return None
        except Exception as e:
            logger.error(f"Error checking open positions: {e}\n")
            return None

    def place_order(self) -> bool:
        # Place a new sell limit order with stop loss and take profit
        try:
            qty = (self.amount / self.order_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            order = self.session.place_order(
                category="linear",
                symbol=self.symbol,
                side="Sell",
                orderType="Limit",
                qty=str(qty),
                price=str(self.order_price),
                stopLoss=str(self.stop_loss_price),
                triggerPrice=str(self.trigger_price),
                leverage=str(self.leverage),
                triggerDirection=2,
                takeProfit=str(self.order_price * Decimal('0.5')),
            )
            logger.info(f"New Order placed: {order}")
            if 'result' in order and 'orderId' in order['result']:
                logger.info(f"Order ID: {order['result']['orderId']}")
            else:
                logger.warning(f"Unexpected order response format: {order}")
            return True
        except Exception as e:
            logger.error(f"Error placing order: {e}\n")
            return False

    def run(self):
        # Main trading loop
        try:
            is_opened_position = False

            while True:
                # Get current market price
                market_price = self.get_market_price()
                if not market_price:
                    time.sleep(5)
                    continue

                # Log current market conditions
                logger.info(
                    f"Market price: {market_price}, Trigger price: {self.trigger_price}, "
                    f"stop loss price: {self.stop_loss_price}, Order price: {self.order_price}"
                )

                # Check for open orders and positions
                order_placed = self.get_open_order()
                open_position = self.get_open_position()
                order_history = self.get_order_history()

                if open_position:
                    is_opened_position = True
                else:
                    if is_opened_position:
                        logger.info("Closing position...")
                        if order_history and order_history[0]["orderStatus"] == "Filled":
                            logger.warning("Position filled")
                        else:
                            logger.warning("Position closed")

                        is_opened_position = False
                    elif not order_placed:
                        # Place a new order if no open orders exist
                        order_placed = self.place_order()

                # Wait before next iteration
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}\n")

if __name__ == "__main__":
    try:
        # Initialize and run the trading bot
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}\n")
