import os
from utils.quotes import Quotes


class Trader(object):
    def __init__(self, max_hold=10, starting_balance=30000):
        self.quotes = Quotes()
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.positions = []

        # get update eod
        self.last_equity = starting_balance
        self.current_reward = 0

        # arbitrary parameters
        self.target_pos_size = 0.1

    def trade_on_signal(self, symbol: str, signal: str, price: float, expiry: str):
        """
        Trades on signal from RL model.
        Buy if bullish. Sell if in position and Bearish.
        Currently does not short on bearish signals.
        """
        pos = [p["symbol"] for p in self.positions]
        if signal == "BULLISH" and symbol not in pos:
            notional = self.last_equity * self.target_pos_size
            qty = notional // price
            value = qty * price
            pos = {
                "qty": qty,
                "entry_price": price,
                "symbol": symbol,
                "cost": qty * price,
                "sell_date": expiry,
            }
            if self.balance > value:
                self.positions.append(pos)
                self.balance -= value

        elif signal == "BEARISH" and symbol in pos:
            to_sell = [p for p in self.positions if p["symbol"] == symbol][0]
            self.balance += to_sell["qty"] * price
            self.positions = [p for p in self.positions if p["symbol"] != symbol]

    def eod(self, day: str):
        # sell positions marked for that day
        for pos in self.positions:
            if pos["sell_date"] == day:
                try:
                    close = self.quotes.get_quote(pos["symbol"], day)
                    self.balance += pos["qty"] * close
                except KeyError:
                    # flat on error
                    self.balance += pos["cost"]

                self.positions = [
                    p for p in self.positions if p["symbol"] != pos["symbol"]
                ]

        self.last_equity = self.balance
        for pos in self.positions:
            try:
                close = self.quotes.get_quote(pos["symbol"], day)
                self.last_equity += pos["qty"] * close
            except KeyError:
                self.last_equity += pos["cost"]

        self.current_reward = (self.last_equity / self.starting_balance - 1) * 100
