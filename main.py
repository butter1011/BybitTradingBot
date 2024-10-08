
import time
import logging
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
        self.symbol = 'BTCUSDT'
        self.trigger_price = Decimal(input("Enter the trigger price: "))
        self.order_price = Decimal(input("Enter the order price: "))
        self.stop_loss_price = self.get_stop_loss_price()
        self.amount = Decimal(input("Enter the amount: "))
        self.leverage = int(input("Enter the leverage: "))
        self.take_profit_price = self.order_price * Decimal('0.5')
        self.trailing_stop = Decimal(input("Enter the trailing stop percentage (e.g., 1 for 1%): ")) / 100

    def get_stop_loss_price(self) -> Decimal:
        user_input = input("Enter the stop loss price (press Enter for default): ")
        if user_input:
            return Decimal(user_input)
        else:
            return self.trigger_price + Decimal('1')

    def run_backtest(data):
        bt = Backtest(data, TradingStrategy, cash=10000, commission=.002)
        stats = bt.run()
        bt.plot()
        return stats

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
                takeProfit=str(self.take_profit_price),
                tpTriggerBy="LastPrice",
                slTriggerBy="LastPrice",
                tpslMode="Full",
                positionIdx=0
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

    def update_trailing_stop(self, position: Dict[str, Any], current_price: Decimal):
        try:
            entry_price = Decimal(position['avgPrice'])
            current_stop_loss = Decimal(position['stopLoss'])
            profit_percentage = (current_price - entry_price) / entry_price

            if profit_percentage > self.trailing_stop:
                new_stop_loss = current_price * (1 - self.trailing_stop)
                if new_stop_loss > current_stop_loss:
                    self.session.set_trading_stop(
                        category="linear",
                        symbol=self.symbol,
                        stopLoss=str(new_stop_loss),
                        positionIdx=0
                    )
                    logger.info(f"Updated trailing stop to: {new_stop_loss}")
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}\n")

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
                    self.update_trailing_stop(open_position, market_price)
                else:
                    if is_opened_position:
                        logger.info("Closing position...")
                        if order_history and order_history[0]["orderStatus"] == "Filled":
                            logger.warning("Position filled")
                        else:
                            logger.warning("Position closed")

                        is_opened_position = False
                    elif not order_placed:
                        if market_price >= self.trigger_price:
                            order_placed = self.place_order()

                time.sleep(0.1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}\n")

if __name__ == "__main__":
    # Load historical data (you need to implement this part)
    # For example:
    # data = pd.read_csv('BTCUSDT_data.csv', index_col='timestamp', parse_dates=True)
    
    # Run the backtest
    # stats = run_backtest(data)
    # print(stats)

    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {e}\n")
