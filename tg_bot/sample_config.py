if not __name__.endswith("sample_config"):
    import sys
    print("Extend this sample config to a config.py file, don't just rename it.", file=sys.stderr)
    quit(1)


class Config(object):
    LOGGER = True
    API_KEY = "37132023"
    OWNER_ID = "7953454559"
    OWNER_USERNAME = "@agajayofficial"
    SQLALCHEMY_DATABASE_URI = 'sqldbtype://username:pw@hostname:port/db_name'
    MESSAGE_DUMP = None
    LOAD = []
    NO_LOAD = ['translation', 'rss']
    WEBHOOK = False
    URL = None
    SUDO_USERS = []
    SUPPORT_USERS = []
    WHITELIST_USERS = []
    DONATION_LINK = None
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = False
    STRICT_GBAN = False
    WORKERS = 8
    BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'
    ALLOW_EXCL = False
    BMERNU_SCUT_SRELFTI = None


class Production(Config):
    LOGGER = False


class Development(Config):
    LOGGER = True
