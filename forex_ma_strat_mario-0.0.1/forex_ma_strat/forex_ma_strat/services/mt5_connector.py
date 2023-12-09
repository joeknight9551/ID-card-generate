import pandas as pd
from datetime import datetime, timedelta
import MetaTrader5 as mt

from forex_ma_strat.logger import Logger


class MT5Connector:
    mt_object = None

    def __init__(self, conf):
        self.login_id = conf["MT5"]["login_id"]
        self.password = conf["MT5"]["password"]
        self.server = conf["MT5"]["server"]
        self.bot_id = conf["MT5"]["bot_id"]

        self.connect_to_mt5()

    def connect_to_mt5(self):
        if not mt.initialize():
            Logger.pprint("initialize() failed")
            mt.shutdown()
            raise Exception('MT5 not initialized')

        if not mt.login(self.login_id, self.password, self.server):
            Logger.pprint("Login failed")
            mt.shutdown()
            raise Exception('Invalid login details')

    def get_ohlc_data(self, symbol_name):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=300)

        ohlc_data = pd.DataFrame(mt.copy_rates_range(symbol_name,
                                                     mt.TIMEFRAME_D1,
                                                     start_date,
                                                     end_date))

        return ohlc_data

    def get_ticker_info(self, ticker):
        ticker_info = mt.symbol_info(ticker)

        return ticker_info

    def get_margin(self):
        free_margin = mt.account_info().balance

        return free_margin

    def get_latest_quote(self, ticker):
        symbol_tick = mt.symbol_info_tick(ticker)

        return symbol_tick
        # return getattr(symbol_tick, bid_ask)

    def get_position(self, ticket):
        position = mt.positions_get(ticket=ticket)

        return position

    def get_pending_order(self, ticket):
        order = mt.orders_get(ticket=ticket)

        return order

    def remove_pending_order(self, ticket):
        request = {
            'action': mt.TRADE_ACTION_REMOVE,
            'order': ticket
        }

        order = mt.order_send(request)

        return order

    def place_order(self, symbol, qty, long_short, price=None, sl=0.0, limit=False, position=None, comment=''):
        Logger.pprint(
            f'{symbol}: Placing {long_short} order, Qty: {qty}, sl: {sl}')

        a = 5
        while a > 0:
            if limit:
                buy_sell = mt.ORDER_TYPE_BUY_LIMIT if long_short == 'Long' else mt.ORDER_TYPE_SELL_LIMIT
                order_type = mt.TRADE_ACTION_PENDING
            else:
                buy_sell = mt.ORDER_TYPE_BUY if long_short == 'Long' else mt.ORDER_TYPE_SELL
                order_type = mt.TRADE_ACTION_DEAL
                price = mt.symbol_info_tick(
                    symbol).ask if long_short == 'Long' else mt.symbol_info_tick(symbol).bid

            request = {
                "action": order_type,
                "symbol": symbol,
                "volume": qty,
                "type": buy_sell,
                "price": price,
                "sl": sl,
                "tp": 0.0,
                "deviation": 20,
                "magic": self.bot_id,
                "comment": comment,
                "type_filling": mt.ORDER_FILLING_IOC
            }

            if position:
                request['position'] = position

            order = mt.order_send(request)

            if order.retcode == 10009:
                return order

            Logger.pprint(f'{symbol}: Error placing order . Retrying')
            a -= 1

        Logger.pprint(
            f'{symbol}: Failed to place order. Order object: {order}')
        Logger.exception(order)

        raise Exception('Could not place order. Check logs')

    def change_sl_tp(self, position, sl=0.0, tp=0.0, comment=''):
        request = {
            'action': mt.TRADE_ACTION_SLTP,
            'position': position,
            'sl': sl,
            'tp': tp,
            'magic': self.bot_id,
            "comment": comment,
            'deviation': 20
        }

        order = mt.order_send(request)

        if order.retcode == 10009:
            Logger.pprint(
                f'SL TP change request success for position {position}')
        else:
            Logger.pprint(
                f'Something went wrong while changing SL/ TP for position {position}')
            Logger.exception(order)

        return order
 