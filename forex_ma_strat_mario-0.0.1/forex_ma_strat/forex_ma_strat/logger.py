import os, logging
from datetime import datetime

class Logger:
    logger = None
    @staticmethod
    def init_logger():
        logger = logging.getLogger('forex_ma_strat')
        logger.setLevel(level=logging.DEBUG)
        fh = logging.StreamHandler()
        fh_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

        path = os.path.join(os.getcwd(), 'log')
        if not os.path.exists(path):
            os.mkdir(path)
        
        filename=os.path.join(path, 'logs_' + datetime.today().strftime('%d_%m_%Y %H%M%S') + '.log')
        fh = logging.FileHandler(filename)
        fh_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

        Logger.logger = logger

        return

    @staticmethod
    def pprint(*messages):
        final_message = ''
        for message in messages:
            if isinstance(message, int) or isinstance(message, float):
                final_message = final_message + ' ' + str(message)
            elif isinstance(message, list):
                final_message = final_message + ' ' + ', '.join(str(x) for x in message)
            elif isinstance(message, str):
                final_message = final_message + ' ' + message
        # print(datetime.now().strftime('%H:%M:%S   ') + final_message)
        Logger.logger.info(final_message)

    @staticmethod
    def exception(e):
        # print(datetime.now().strftime('%H:%M:%S    ') + str(e))
        Logger.logger.exception(e)
