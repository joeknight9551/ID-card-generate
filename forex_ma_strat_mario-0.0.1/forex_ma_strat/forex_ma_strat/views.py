# HttpResponse is used to render the response HTTP Request
from django.http import HttpResponse
from django.shortcuts import render
# Function is being initialised to perform a return request when called

from forex_ma_strat.global_data import GlobalData as gd
from forex_ma_strat.services.strategy import Strategy
from forex_ma_strat.config import Config

def index(request):
    print(gd.symbols)
    return HttpResponse('Welcome')

def get_trades(request):
    gd.trades = []
    conf = Config()
    config = conf.get_config()
    strat = Strategy(config['symbols'])
    strat.run()

    return render(request, 'trades.html', {'trades': gd.trades})

def trigger_trade(request):
    # gd.trades = []
    try:
        ticker = request.GET['ticker']
        conf = Config()
        config = conf.get_config()
        strat = Strategy(config['symbols'])

        strat.trigger_trade(ticker)

        return HttpResponse(f'Trade taken for {ticker}')
    except Exception as ex:
        return HttpResponse(str(ex))

