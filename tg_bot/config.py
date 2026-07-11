import os

class Config(object):
    LOGGER = True
    API_KEY = os.environ.get("BOT_TOKEN", None)
    OWNER_ID = 804035903
    
    CHANNEL_LINK = "Amazon_Deal_Here"
    CHANNEL_LINK_2 = "DARKGLOBALNET"

class Production(Config):
    LOGGER = False

class Development(Config):
    LOGGER = True
