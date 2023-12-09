import json
import os

from forex_ma_strat.logger import Logger


class Config:
    """
    Config management class
    """

    def __init__(self, filename: str = os.path.join(os.getcwd(), "config.json")):
        self.filename = filename
        self.config = {}

    def read_config(self) -> bool:
        """
        Read config from file
        """
        try:
            with open(self.filename) as f:
                self.config = json.load(f)
                return True
            Logger.pprint("Okay import config file.")
        except Exception as e:
            Logger.pprint('Error fetching config file', e)
            Logger.exception(e)
            return False

    def get_config(self) -> dict:
        """
        Get config controller function
        """
        success = self.read_config()
        if success:
            return self.config

        return {}
