
import time
import logging
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN
from typing import Optional, Dict, Any

class TradingBot:
    def __init__(self):
        # ... (existing initialization)
        self.retracement_percentage = Decimal(input("Enter the retracement percentage (0-100): ")) / 100

    # ... (existing methods)

    def calculate_retracement_price(self, high_price: Decimal, low_price: Decimal) -> Decimal:
        price_range = high_price - low_price
        retracement_amount = price_range * self.retracement_percentage
        return high_price - retracement_amount

    def place_retracement_order(self, retracement_price: Decimal) -> bool:
        try:
            qty = (self.amount / retracement_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            order = self.session.place_order(
                category="linear",
                symbol=self.symbol,
                side="Buy",
                orderType="Limit",
                qty=str(qty),
                price=str(retracement_price),
                stopLoss=str(self.stop_loss_price),
                takeProfit=str(retracement_price * Decimal('1.5')),
                leverage=str(self.leverage),
            )
            logger.info(f"Retracement Order placed: {order}")
            if 'result' in order and 'orderId' in order['result']:
                logger.info(f"Retracement Order ID: {order['result']['orderId']}")
            else:
                logger.warning(f"Unexpected retracement order response format: {order}")
            return True
        except Exception as e:
            logger.error(f"Error placing retracement order: {e}\n")
            return False

    def run(self):
        try:
            is_opened_position = False
            high_price = Decimal('-Infinity')
            low_price = Decimal('Infinity')

            while True:
                market_price = self.get_market_price()
                if not market_price:
                    time.sleep(5)
                    continue

                high_price = max(high_price, market_price)
                low_price = min(low_price, market_price)

                logger.info(
                    f"Market price: {market_price}, High: {high_price}, Low: {low_price}, "
                    f"Trigger price: {self.trigger_price}, Stop loss: {self.stop_loss_price}, "
                    f"Order price: {self.order_price}"
                )

                retracement_price = self.calculate_retracement_price(high_price, low_price)
                logger.info(f"Calculated retracement price: {retracement_price}")

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
                        high_price = Decimal('-Infinity')
                        low_price = Decimal('Infinity')
                    elif not order_placed:
                        if market_price <= retracement_price:
                            self.place_retracement_order(retracement_price)
                        else:
                            self.place_order()

                time.sleep(0.1)
        except Exception as e:
            logger.error(f"An error occurred in run: {e}\n")