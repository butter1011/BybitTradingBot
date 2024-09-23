
import time
import logging
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

class TradingBot:
    def __init__(self):
        self.session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
        self.symbol = 'BTCUSDT'
        self.trigger_price = self._get_decimal_input("Enter the trigger price: ")
        self.order_price = self._get_decimal_input("Enter the order price: ")
        self.stop_loss_price = self._get_stop_loss_price()
        self.amount = self._get_decimal_input("Enter the amount: ")
        self.leverage = self._get_integer_input("Enter the leverage: ")

    def _get_decimal_input(self, prompt: str) -> Decimal:
        while True:
            try:
                return Decimal(input(prompt))
            except ValueError:
                print("Invalid input. Please enter a valid number.")

    def _get_integer_input(self, prompt: str) -> int:
        while True:
            try:
                return int(input(prompt))
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

    def _get_stop_loss_price(self) -> Decimal:
        user_input = input("Enter the stop loss price (press Enter for default): ")
        return Decimal(user_input) if user_input else self.trigger_price + Decimal('1')

    def get_market_price(self) -> Optional[Decimal]:
        try:
            ticker = self.session.get_tickers(category="linear", symbol=self.symbol)
            return Decimal(ticker["result"]["list"][0]["lastPrice"])
        except Exception as e:
            logger.error(f"Error getting market price: {e}")
            return None

    def get_open_order(self) -> Optional[Dict[str, Any]]:
        try:
            orders = self.session.get_open_orders(category="linear", symbol=self.symbol)
            for order in orders["result"]["list"]:
                if order["orderType"] == "Limit" and order["side"] == "Sell":
                    logger.info(f"Found open order: {order['orderStatus']}")
                    return order
            return None
        except Exception as e:
            logger.error(f"Error checking open orders: {e}")
            return None

    def get_order_history(self) -> Optional[list[Dict[str, Any]]]:
        try:
            order_history = self.session.get_order_history(category="linear", symbol=self.symbol, limit=1)
            return order_history["result"]["list"]
        except Exception as e:
            logger.error(f"Error checking order history: {e}")
            return None

    def get_open_position(self) -> Optional[Dict[str, Any]]:
        try:
            positions = self.session.get_positions(category="linear", symbol=self.symbol)
            for pos in positions["result"]["list"]:
                if pos["stopLoss"]:
                    logger.info(f"Found position... {pos['curRealisedPnl']}")
                    return pos
            return None
        except Exception as e:
            logger.error(f"Error checking open positions: {e}")
            return None

    def place_order(self) -> bool:
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
            logger.error(f"Error placing order: {e}")
            return False

    def run(self):
        try:
            is_opened_position = False

            while True:
                market_price = self.get_market_price()
                if not market_price:
                    time.sleep(5)
                    continue

                logger.info(
                    f"Market price: {market_price}, Trigger price: {self.trigger_price}, "
                    f"Stop loss price: {self.stop_loss_price}, Order price: {self.order_price}"
                )

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
                        self.place_order()

                time.sleep(0.1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}")

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}")
