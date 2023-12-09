import numpy as np
import decimal
import time as t
import json
import os
from datetime import datetime, timezone, time
from threading import Thread

from forex_ma_strat.logger import Logger
from forex_ma_strat.services.mt5_connector import MT5Connector
from forex_ma_strat.global_data import GlobalData as gd


class Strategy:
    def __init__(self, symbols):
        self.symbols = symbols
        Logger.pprint('Strategy initialized')

    def __find_decimals(self, value):
        return (abs(decimal.Decimal(str(value)).as_tuple().exponent))

    def calc_df(self, symbol_name):
        df = MT5Connector.mt_object.get_ohlc_data(symbol_name)
        df['signal'] = np.where(df['close'] > df['high'].shift(), 1, 0)
        df['signal'] = np.where(
            df['close'] < df['low'].shift(), -1, df['signal'])
        # df['9ema'] = df['close'].ewm(span=9, adjust=False).mean()
        # df['15ema'] = df['close'].ewm(span=15, adjust=False).mean()
        # df['signal'] = np.where((df['9ema'] > df['15ema']) & (
        #     df['9ema'].shift() < df['15ema'].shift()), 1, 0)
        # df['signal'] = np.where((df['9ema'] < df['15ema']) & (
        #     df['9ema'].shift() > df['15ema'].shift()), -1, df['signal'])

        df['h-l'] = df['high'] - df['low']
        df['10ema'] = df['h-l'].ewm(span=10,
                                    adjust=False, ignore_na=True).mean()
        df['10ema_test'] = df['h-l'].ewm(span=10,
                                         adjust=True, ignore_na=True).mean()
        df['100ema'] = df['10ema'].ewm(
            span=100, adjust=False, ignore_na=True).mean()
        df['100ema_test'] = df['10ema_test'].ewm(
            span=100, adjust=True, ignore_na=True).mean()
        df['stdev'] = df['h-l'].rolling(100).std()
        df['stdev_test'] = 0.5*df['h-l'].rolling(100).std()

        df['span_calc'] = df['100ema'] + 0.5 * df['stdev']
        df['span_calc_test'] = df['100ema_test'] + 0.5 * df['stdev']
        df['span_calc'] = df['span_calc'].shift()

        # df['h-l'] = df['h-l'].rolling(21).mean().shift()

        if datetime.now(timezone.utc).time() < time(2, 0):
            df['signal'] = df['signal'].shift()

        if df['signal'].values[-1]:
            trade = {
                'symbol_name': symbol_name,
                'type': 'Long' if df['signal'].values[-1] == 1 else 'Short'
            }
            gd.trades.append(trade)

        gd.df[symbol_name] = df.copy()

        return

    def run(self):
        for symb in self.symbols:
            self.calc_df(symb)

    def __norm_trade_size(self, trade_size, sym_min_lot, sym_max_lot, volume_step):
        if trade_size < sym_min_lot:
            trade_size = sym_min_lot
        elif trade_size > sym_max_lot:
            trade_size = sym_max_lot
        else:
            trade_size = round(trade_size/volume_step) * volume_step

        return trade_size

    def trigger_trade(self, ticker):
        curr_datetime_str = datetime.utcnow().date().strftime('%d%m%Y')
        if curr_datetime_str not in gd.day_trading_symbols:
            gd.day_trading_symbols[curr_datetime_str] = []
        else:
            if ticker in gd.day_trading_symbols[curr_datetime_str]:
                raise Exception(f'Trade already taken for {ticker} today')

        symbol_info = MT5Connector.mt_object.get_ticker_info(ticker)
        trade_tick_size = symbol_info.trade_tick_size
        margin = MT5Connector.mt_object.get_margin()

        day_range = gd.df[ticker].iloc[-2]['span_calc']
        ticker_ob = next(
            filter(lambda x: x['symbol_name'] == ticker, gd.trades))
        bid_ask = 'ask' if ticker_ob['type'] == 'Long' else 'bid'

        latest_price = MT5Connector.mt_object.get_latest_quote(ticker)

        # Risk calculation
        # spread = latest_price.ask - latest_price.bid
        # span1 = (day_range+spread)
        # span2 = (day_range+spread - 0.4 * day_range)

        # order1_risk = span1 * symbol_info.trade_tick_value * 2
        # order2_risk = span2 * symbol_info.trade_tick_value * 5
        risk_point1 = (day_range) * 2/symbol_info.point
        risk_point2 = (day_range - 0.4 * day_range) * 5 / \
            symbol_info.point

        if (risk_point1 + risk_point2) * symbol_info.trade_tick_value == 0:
            pass
        else:
            trade1_size = 2 * margin / \
                (100 * (risk_point1 + risk_point2) * symbol_info.trade_tick_value)
            # trade2_size = 70 * margin / \
            #     (10000 * (risk_point1 + risk_point2) * symbol_info.trade_tick_value)

            # trade1_size = 2 * margin / \
            #     (100 * (risk_point1 + risk_point2) * symbol_info.trade_tick_value)
            # trade2_size = 5 * margin / \
            #     (100 * (risk_point1 + risk_point2) * symbol_info.trade_tick_value)

        trade1_size = self.__norm_trade_size(
            trade1_size, symbol_info.volume_min, symbol_info.volume_max, symbol_info.volume_step)

        # trade2_size = trade1_size * 2.5
        # trade2_size = self.__norm_trade_size(
        #     trade2_size, symbol_info.volume_min, symbol_info.volume_max, symbol_info.volume_step)

        # For minimum qty
        if trade1_size == symbol_info.volume_min:
            trade1_size *= 2

            trade1_size = self.__norm_trade_size(
                trade1_size, symbol_info.volume_min, symbol_info.volume_max, symbol_info.volume_step)

        trade2_size = trade1_size * 2.5
        trade2_size = self.__norm_trade_size(
            trade2_size, symbol_info.volume_min, symbol_info.volume_max, symbol_info.volume_step)

        latest_price = getattr(latest_price, bid_ask)
        if ticker_ob['type'] == 'Long':
            sl = round(round((latest_price - day_range) / trade_tick_size)
                       * trade_tick_size, self.__find_decimals(trade_tick_size))
        else:
            sl = round(round((latest_price + day_range) / trade_tick_size)
                       * trade_tick_size, self.__find_decimals(trade_tick_size))
        order1 = MT5Connector.mt_object.place_order(
            ticker, trade1_size, ticker_ob['type'], latest_price, sl, comment='stage1')

        # 70% order
        if ticker_ob['type'] == 'Long':
            # second_order_price = order1.price - ((order1.price - sl) * 0.4)
            second_order_price = order1.price - day_range * 0.4
        else:
            # second_order_price = order1.price + ((sl - order1.price) * 0.4)
            second_order_price = order1.price + day_range * 0.4

        second_order_price = round(round(second_order_price/trade_tick_size)
                                   * trade_tick_size, self.__find_decimals(trade_tick_size))

        order2 = MT5Connector.mt_object.place_order(
            ticker, trade2_size, ticker_ob['type'], second_order_price, sl, limit=True, comment='stage1')

        # Place tp for first order
        if ticker_ob['type'] == 'Long':
            half_tp = order1.price + day_range * 0.2
            stage_2_breakeven = order1.price - day_range * 0.2
            # stage_2_breakeven = second_order_price + \
            #     day_range * 0.2 + second_order_price * 0.0005
        else:
            half_tp = order1.price - day_range * 0.2
            stage_2_breakeven = order1.price + day_range * 0.2
            # stage_2_breakeven = second_order_price - \
            #     day_range * 0.2 - second_order_price * 0.0005

        stage_2_breakeven = round(round(stage_2_breakeven/trade_tick_size)
                                  * trade_tick_size, self.__find_decimals(trade_tick_size))

        res = {
            'ticker': ticker,
            'type': ticker_ob['type'],
            'order1_price': order1.price,
            'order1_half_tp': half_tp,
            'order1_position': order1.order,
            'order1_qty': trade1_size,
            'order2_price': second_order_price,
            'order2_position': order2.order,
            'order2_qty': trade2_size,
            'stage_2_breakeven': stage_2_breakeven,
            'sl': sl,
            'current_stage': 1,
            'avg_hl': day_range,
            'datetime_str': curr_datetime_str
        }

        gd.new_trade_event.wait()
        gd.active_trades.append(res)
        gd.day_trading_symbols[curr_datetime_str].append(ticker)

        Logger.pprint(f'{ticker}: Successfully placed stage 1 trades')
        Logger.pprint(f'{ticker} USD point: {symbol_info.trade_tick_value}')
        Logger.pprint(f'{ticker} res: {res}')
        return

    def __handle_stage_1(self, trade):
        try:
            ticker = trade['ticker']
            position = MT5Connector.mt_object.get_position(
                trade['order1_position'])
            curr_pending_order = MT5Connector.mt_object.get_pending_order(
                trade['order2_position'])

            if not len(position) and not len(curr_pending_order):
                # Position exited manually
                Logger.pprint(f'{ticker} position not found')
                return None
            if not len(position):
                # Position exited manually, but order still remaining
                # Remove order
                Logger.pprint(
                    f'{ticker} position not found. Removing pending order')

                MT5Connector.mt_object.remove_pending_order(
                    trade['order2_position'])
                return None

            if not len(curr_pending_order):
                position2 = MT5Connector.mt_object.get_position(
                    trade['order2_position'])

                if len(position2):
                    Logger.pprint(f'{ticker} trade update. Moving to stage 2')
                    # Change tp for trade 1
                    # MT5Connector.mt_object.change_sl_tp(
                    #     trade['order1_position'], trade['sl'], trade['stage_2_breakeven'], comment='stage2')
                    trade['current_stage'] = 2

                    return trade

            curr_quote = MT5Connector.mt_object.get_latest_quote(ticker)

            side = None
            if trade['type'] == 'Long':
                price = curr_quote.bid
                if price >= trade['order1_half_tp']:
                    side = 'Short'
                    sl = trade['order1_price'] * 1.00025

            elif trade['type'] == 'Short':
                price = curr_quote.ask
                # half tp triggered
                if price <= trade['order1_half_tp']:
                    side = 'Long'
                    sl = trade['order1_price'] * 0.99975

            if side:
                Logger.pprint(f'{ticker} trade update. Moving to stage 3')
                symbol_info = MT5Connector.mt_object.get_ticker_info(ticker)
                trade_tick_size = symbol_info.trade_tick_size
                sl = round(round(sl/trade_tick_size)
                        * trade_tick_size, self.__find_decimals(trade_tick_size))

                close_qty = position[0].volume / 2

                close_qty = self.__norm_trade_size(
                    close_qty, symbol_info.volume_min, symbol_info.volume_max, symbol_info.volume_step)
                Logger.pprint(
                    f'{ticker} trade update. Closing half positions for order 1. Qty: {close_qty}')
                order = MT5Connector.mt_object.place_order(
                    ticker, close_qty, side, position=trade['order1_position'], comment='stage3')
                Logger.pprint(f'{ticker} trade update. Removing limit order')
                MT5Connector.mt_object.remove_pending_order(
                    trade['order2_position'])

                Logger.pprint(
                    f'{ticker} trade update. Changing sl for order 1 to {sl}')
                MT5Connector.mt_object.change_sl_tp(
                    trade['order1_position'], sl, comment='stage3')

                today_date = datetime.utcnow().date().strftime('%d%m%Y')
                trade['last_trail_dt'] = today_date
                trade['stage3_pos'] = 'order1'
                trade['current_stage'] = 3

            return trade
        except Exception as e:
            Logger.exception(f'Something went wrong in handling stage 1')
            Logger.exception(trade)

            return trade

    def __handle_stage_2(self, trade):
        try:
            ticker = trade['ticker']
            position1 = MT5Connector.mt_object.get_position(
                trade['order1_position'])
            position2 = MT5Connector.mt_object.get_position(
                trade['order2_position'])

            if not len(position1) and not len(position2):
                Logger.pprint(f'{ticker} position is closed.')
                return None

            curr_quote = MT5Connector.mt_object.get_latest_quote(ticker)

            side = None
            if trade['type'] == 'Long':
                price = curr_quote.bid
                if price >= trade['stage_2_breakeven']:
                    side = 'Short'
                    sl = trade['order2_price'] * 1.00005

            elif trade['type'] == 'Short':
                price = curr_quote.ask
                if price <= trade['stage_2_breakeven']:
                    side = 'Long'
                    sl = trade['order2_price'] * 0.99995

            if side:
                Logger.pprint(
                    f'{ticker} trade update. Moving from stage 2 to stage 3')
                symbol_info = MT5Connector.mt_object.get_ticker_info(ticker)
                trade_tick_size = symbol_info.trade_tick_size
                sl = round(round(sl/trade_tick_size)
                        * trade_tick_size, self.__find_decimals(trade_tick_size))

                # Calculating quantity for order 2
                qty = 4/5 * trade['order2_qty']
                qty = self.__norm_trade_size(
                    qty, symbol_info.volume_min, symbol_info.volume_max, symbol_info.volume_step)

                # Close position 1
                Logger.pprint(
                    f'{ticker} trade update. Closing Position 1.')
                order_1 = MT5Connector.mt_object.place_order(
                    ticker, trade['order1_qty'], side, position=trade['order1_position'])

                # closing second position partially
                Logger.pprint(
                    f'{ticker} trade update. Closing some positions for order 2. Qty: {trade["order1_qty"]}')
                order = MT5Connector.mt_object.place_order(
                    ticker, qty, side, position=trade['order2_position'], comment="stage3")
                Logger.pprint(
                    f'{ticker} trade update. Changing sl for order 2 to {sl}')
                MT5Connector.mt_object.change_sl_tp(
                    trade['order2_position'], sl, comment='stage3')

                today_date = datetime.utcnow().date().strftime('%d%m%Y')
                trade['last_trail_dt'] = today_date
                trade['stage3_pos'] = 'order2'
                trade['current_stage'] = 3

            return trade
    
        except Exception as e:
            Logger.exception(f'Something went wrong in handling stage 2')
            Logger.exception(trade)

            return trade

    def __handle_stage_3(self, trade):
        try:
            ticker = trade['ticker']
            curr_trade = trade[f'{trade["stage3_pos"]}_position']
            position = MT5Connector.mt_object.get_position(
                curr_trade)

            if not len(position):
                Logger.pprint(f'{ticker} position is closed.')
                return None

            if 'last_trail_dt' not in trade:
                trade['last_trail_dt'] = trade['datetime_str']

            today_date = datetime.utcnow().date().strftime('%d%m%Y')

            if today_date != trade['last_trail_dt']:
                df = MT5Connector.mt_object.get_ohlc_data(ticker)
                new_sl = None
                if trade['type'] == 'Long':
                    sl = df.iloc[-2]['low']
                    if sl > position[0].sl and position[0].price_current > sl:
                        new_sl = sl
                else:
                    sl = df.iloc[-2]['high']
                    if sl < position[0].sl and position[0].price_current < sl:
                        new_sl = sl

                if new_sl:
                    Logger.pprint(
                        f'{ticker} trade update. Daily SL trail. Changing sl for {trade["stage3_pos"]} to {new_sl}')
                    MT5Connector.mt_object.change_sl_tp(
                        curr_trade, new_sl, comment='stage3 trail sl')

                trade['last_trail_dt'] = today_date

            return trade
        except Exception as e:
            Logger.exception(f'Something went wrong in handling stage 3')
            Logger.exception(trade)

            return trade

    def __handle_trade_management(self, data):
        if gd.new_trade_event.is_set():
            gd.new_trade_event.clear()
        new_data = []
        for trade in data:
            pass
            if trade['current_stage'] == 1:
                t = self.__handle_stage_1(trade)
            elif trade['current_stage'] == 2:
                t = self.__handle_stage_2(trade)
            elif trade['current_stage'] == 3:
                t = self.__handle_stage_3(trade)

            if t:
                new_data.append(t)

        # Work with the file and refill active trades
        with open('data.json', 'w') as f:
            json.dump(new_data, f)

        gd.active_trades = new_data
        gd.new_trade_event.set()
        
        return new_data

    def init_active_trades(self):
        Logger.pprint('Fetching existing trades and reloading variables')

        if not os.path.exists("data.json"):
            Logger.pprint('No data file found.')
            return

        with open('data.json', 'r') as f:
            data = json.load(f)

        trades = self.__handle_trade_management(data)

        # Loop for curr day trades
        for trade in trades:
            trade_datetime = trade['datetime_str']
            curr_datetime = datetime.utcnow().date().strftime('%d%m%Y')

            if trade_datetime != curr_datetime:
                continue

            if trade_datetime not in gd.day_trading_symbols:
                gd.day_trading_symbols[trade_datetime] = []

            gd.day_trading_symbols[trade_datetime].append(trade['ticker'])

        return

    def order_management_loop(self):
        Logger.pprint('Order management loop started')
        while True:
            try:
                data = gd.active_trades

                trades = self.__handle_trade_management(data)
            except Exception as e:
                Logger.pprint(
                    f'Exception occured in Order management loop. Exception: {e}')
                Logger.exception(str(e))

            t.sleep(5)

    def order_management_loop_controller(self):
        # Run this on a thread
        Thread(target=self.order_management_loop).start()
        return
