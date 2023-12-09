"""forex_ma_strat URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from forex_ma_strat.logger import Logger
from forex_ma_strat.services.mt5_connector import MT5Connector
from forex_ma_strat.services.strategy import Strategy
from forex_ma_strat.config import Config
from forex_ma_strat.global_data import GlobalData as gd
from forex_ma_strat.views import index, get_trades, trigger_trade

urlpatterns = [
    path("", index, name='index'),
    path("run", get_trades, name='get_trades'),
    path("trigger", trigger_trade, name='trigger'),
]

Logger.init_logger()
conf = Config()
config = conf.get_config()
MT5Connector.mt_object = MT5Connector(config)
gd.symbols = config["symbols"]

strat = Strategy(config["symbols"])
strat.init_active_trades()
strat.order_management_loop_controller()
# Run order management
#one time run code