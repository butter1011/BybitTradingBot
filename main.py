
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
        self.strategy = input("Enter the strategy (MA, RSI, or MACD): ").upper()
        self.ma_period = 20 if self.strategy == 'MA' else None
        self.rsi_period = 14 if self.strategy == 'RSI' else None
        self.macd_fast = 12 if self.strategy == 'MACD' else None
        self.macd_slow = 26 if self.strategy == 'MACD' else None
        self.macd_signal = 9 if self.strategy == 'MACD' else None

    def calculate_ma(self, data, period):
        return sum(data[-period:]) / period

    def calculate_rsi(self, data, period):
        deltas = [data[i] - data[i-1] for i in range(1, len(data))]
        gain = [d if d > 0 else 0 for d in deltas]
        loss = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gain[-period:]) / period
        avg_loss = sum(loss[-period:]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, data, fast, slow, signal):
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        return macd_line[-1], signal_line[-1]

    def calculate_ema(self, data, period):
        multiplier = 2 / (period + 1)
        ema = [data[0]]
        for price in data[1:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        return ema

    def get_historical_data(self, limit=100):
        try:
            kline = self.session.get_kline(
                category="linear",
                symbol=self.symbol,
                interval=15,
                limit=limit
            )
            return [Decimal(candle[4]) for candle in kline["result"]["list"]]
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None

    def should_enter_trade(self):
        historical_data = self.get_historical_data()
        if not historical_data:
            return False

        if self.strategy == 'MA':
            ma = self.calculate_ma(historical_data, self.ma_period)
            return historical_data[-1] > ma

        elif self.strategy == 'RSI':
            rsi = self.calculate_rsi(historical_data, self.rsi_period)
            return rsi < 30  # Oversold condition

        elif self.strategy == 'MACD':
            macd, signal = self.calculate_macd(historical_data, self.macd_fast, self.macd_slow, self.macd_signal)
            return macd > signal  # Bullish crossover

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
                        if self.should_enter_trade():
                            order_placed = self.place_order()
                            logger.info(f"Entered trade based on {self.strategy} strategy")
                        else:
                            logger.info(f"Waiting for {self.strategy} strategy signal")

                time.sleep(0.1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}\n")

if __name__ == "__main__":
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}\n")