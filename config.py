import os

class Config(object):
    LOGGER = True
    API_KEY = os.environ.get("BOT_TOKEN", None)
    OWNER_ID = 8804035903  # आपकी टेलीग्राम आईडी
    
    # यहाँ नीचे अपने टेलीग्राम चैनल का लिंक (Username) डालिए
    # उदाहरण के लिए अगर चैनल @MyChannel है, तो सिर्फ 'MyChannel' लिखें
    CHANNEL_LINK = "Amazon_Deal_Here" 
    CHANNEL_LINK_2 = "DARKGLOBALNET"

class Production(Config):
    LOGGER = False

class Development(Config):
    LOGGER = True
