
import time
import logging
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
API_KEY = 'r20vk2T6FIl5BhVgg4'
API_SECRET = 'sRL0lTzifGRIlMhHZIBCEs5RbQbeeUz4DD2R'

class TradingBot:
    def __init__(self):
        self.session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
        self.symbol = 'BTCUSDT'
        self.trigger_price = Decimal(input("Enter the trigger price: "))
        self.order_price = Decimal(input("Enter the order price: "))
        self.stop_loss_price = self.get_stop_loss_price()
        self.amount = Decimal(input("Enter the amount: "))
        self.leverage = int(input("Enter the leverage: "))
        self.monitoring_interval = int(input("Enter monitoring interval in seconds: "))

    def monitor_price(self):
        while True:
            market_price = self.get_market_price()
            if market_price:
                logger.info(f"Current market price: {market_price}")
                if market_price >= self.trigger_price:
                    logger.warning(f"Trigger price {self.trigger_price} reached!")
                    return True
            time.sleep(self.monitoring_interval)

    def run(self):
        try:
            is_opened_position = False

            logger.info("Starting price monitoring...")
            if self.monitor_price():
                logger.info("Trigger price reached. Starting trading operations.")

            while True:
                market_price = self.get_market_price()
                if not market_price:
                    time.sleep(5)
                    continue

                logger.info(
                    f"Market price: {market_price}, Trigger price: {self.trigger_price}, "
                    f"stop loss price: {self.stop_loss_price}, Order price: {self.order_price}"
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
                        order_placed = self.place_order()

                time.sleep(0.1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}\n")

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}\n")
