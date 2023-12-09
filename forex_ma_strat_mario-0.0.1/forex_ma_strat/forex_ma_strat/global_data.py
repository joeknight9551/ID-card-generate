from threading import Event

class GlobalData:
    symbols = []

    # Current available trades
    trades = []
    new_trade_event = Event()

    df = {}
    active_trades = []
    day_trading_symbols = {}
