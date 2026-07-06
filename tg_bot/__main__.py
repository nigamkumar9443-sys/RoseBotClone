import importlib
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import Forbidden, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler, filters, MessageHandler, CallbackQueryHandler
from telegram.ext import Application
from tg_bot.modules.helper_funcs.string_handling import escape_markdown

from tg_bot import application, TOKEN, WEBHOOK, OWNER_ID, DONATION_LINK, CERT_PATH, PORT, URL, LOGGER, \
    ALLOW_EXCL
from tg_bot.modules import ALL_MODULES
from tg_bot.modules.helper_funcs.chat_status import is_user_admin
from tg_bot.modules.helper_funcs.misc import paginate_modules

PM_START_TEXT = """

*HI {}, MY NAME IS {}!*

*I Am A Cool Admin Bot Maintained By* [FADIL](tg://user?id={}) 

*I'm here to help you manage your groups!Hit /help to find out more about how to use me to my full potential.*

*JOIN OUR GROUP*
"""

HELP_STRINGS = """
Hey there! My name is *{bot_name}*.

*Main* commands available:
 - /start: start the bot
 - /help: PM's you this message.
 - /help <module name>: PM's you info about that module.
 - /donate: information about how to donate!
 - /settings:
   - in PM: will send you your settings for all supported modules.
   - in a group: will redirect you to pm, with all that chat's settings.
{excl}
And the following:
"""

def get_help_str():
    return HELP_STRINGS.format(
        bot_name=application.bot.first_name,
        excl="" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n"
    )

DONATE_STRING = """ *🙋‍♂️Hello Bro or Sis*!

*😎Contect @agajayofficial*

*👉Clcik 👉 /donate*
"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("tg_bot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

from tg_bot.modules.sql import BASE
from tg_bot import DB_URI
if DB_URI:
    from sqlalchemy import create_engine
    _engine = create_engine(DB_URI)
    BASE.metadata.create_all(_engine)
    _engine.dispose()

async def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    await application.bot.send_message(chat_id=chat_id,
                                       text=text,
                                       parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=keyboard)


async def test(update: Update, context):
    update.effective_message.reply_text("This person edited a message")


async def start(update: Update, context):
    args = context.args or []
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                await send_help(update.effective_chat.id, get_help_str())

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = application.bot.getChat(match.group(1))

                if await is_user_admin(chat, update.effective_user.id):
                    await send_settings(match.group(1), update.effective_user.id, False)
                else:
                    await send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            await update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(first_name), escape_markdown(application.bot.first_name), OWNER_ID),
                parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="⭕️ Command Help ⭕️", url="https://t.me/{}?start=help".format(application.bot.username))],
                     [InlineKeyboardButton(text="📢GROUP", url="https://t.me/tmedping"), InlineKeyboardButton(text="🤠Credits", url="http://t.me/fadil_mk")],
                     [InlineKeyboardButton(text="➕ Add me to your group ➕", url="t.me/{}?startgroup=true".format(application.bot.username))]]))
    else:
        await update.effective_message.reply_text("I AM ALIVE")


def error_callback(bot, update, error):
    try:
        raise error
    except Forbidden:
        print(error)
    except BadRequest:
        print("BadRequest caught")
        print(error)
    except TimedOut:
        pass
    except NetworkError:
        pass
    except ChatMigrated as err:
        print(err)
    except TelegramError:
        print(error)


async def help_button(update: Update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = "Here is the help for the *{}* module:\n".format(HELPABLE[module].__mod_name__) \
                   + HELPABLE[module].__help__
            await query.message.reply_text(text=text,
                                           parse_mode=ParseMode.MARKDOWN,
                                           reply_markup=InlineKeyboardMarkup(
                                               [[InlineKeyboardButton(text="🔙 Back 🔙", callback_data="help_back")]]))

        elif prev_match:
            curr_page = int(prev_match.group(1))
            await query.message.reply_text(get_help_str(),
                                           parse_mode=ParseMode.MARKDOWN,
                                           reply_markup=InlineKeyboardMarkup(
                                               paginate_modules(curr_page - 1, HELPABLE, "help")))

        elif next_match:
            next_page = int(next_match.group(1))
            await query.message.reply_text(get_help_str(),
                                           parse_mode=ParseMode.MARKDOWN,
                                           reply_markup=InlineKeyboardMarkup(
                                               paginate_modules(next_page + 1, HELPABLE, "help")))

        elif back_match:
            await query.message.reply_text(text=get_help_str(),
                                           parse_mode=ParseMode.MARKDOWN,
                                           reply_markup=InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")))

        await context.bot.answer_callback_query(query.id)
        await query.message.delete()
    except BadRequest as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.exception("Exception in help buttons. %s", str(query.data))


async def get_help(update: Update, context):
    chat = update.effective_chat
    args = update.effective_message.text.split(None, 1)

    if chat.type != chat.PRIVATE:
        update.effective_message.reply_text("Contact me in PM to get the list of possible commands.",
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="💫 Help 💫",
                                                                       url="t.me/{}?start=help".format(
                                                                           application.bot.username))]]))
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = "Here is the available help for the *{}* module:\n".format(HELPABLE[module].__mod_name__) \
               + HELPABLE[module].__help__
        await send_help(chat.id, text, InlineKeyboardMarkup([[InlineKeyboardButton(text="Back", callback_data="help_back")]]))

    else:
        await send_help(chat.id, get_help_str())


async def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id)) for mod in USER_SETTINGS.values())
            await application.bot.send_message(user_id, "These are your current settings:" + "\n\n" + settings,
                                               parse_mode=ParseMode.MARKDOWN)
        else:
            await application.bot.send_message(user_id, "Seems like there aren't any user specific settings available :'(",
                                               parse_mode=ParseMode.MARKDOWN)
    else:
        if CHAT_SETTINGS:
            chat_name = (await application.bot.get_chat(chat_id)).title
            await application.bot.send_message(user_id,
                                               text="Which module would you like to check {}'s settings for?".format(
                                                   chat_name),
                                               reply_markup=InlineKeyboardMarkup(
                                                   paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)))
        else:
            await application.bot.send_message(user_id, "Seems like there aren't any chat settings available :'(\nSend this "
                                               "in a group chat you're admin in to find its current settings!",
                                               parse_mode=ParseMode.MARKDOWN)


async def settings_button(update: Update, context):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = await context.bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(escape_markdown(chat.title),
                                                                                      CHAT_SETTINGS[module].__mod_name__) + \
                   CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            await query.message.reply_text(text=text,
                                           parse_mode=ParseMode.MARKDOWN,
                                           reply_markup=InlineKeyboardMarkup(
                                               [[InlineKeyboardButton(text="Back",
                                                                      callback_data="stngs_back({})".format(chat_id))]]))

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = await context.bot.get_chat(chat_id)
            await query.message.reply_text("Hi there! There are quite a few settings for {} - go ahead and pick what "
                                           "you're interested in.".format(chat.title),
                                           reply_markup=InlineKeyboardMarkup(
                                               paginate_modules(curr_page - 1, CHAT_SETTINGS, "stngs",
                                                                chat=chat_id)))

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = await context.bot.get_chat(chat_id)
            await query.message.reply_text("Hi there! There are quite a few settings for {} - go ahead and pick what "
                                           "you're interested in.".format(chat.title),
                                           reply_markup=InlineKeyboardMarkup(
                                               paginate_modules(next_page + 1, CHAT_SETTINGS, "stngs",
                                                                chat=chat_id)))

        elif back_match:
            chat_id = back_match.group(1)
            chat = await context.bot.get_chat(chat_id)
            await query.message.reply_text(text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                                                "you're interested in.".format(escape_markdown(chat.title)),
                                           parse_mode=ParseMode.MARKDOWN,
                                           reply_markup=InlineKeyboardMarkup(paginate_modules(0, CHAT_SETTINGS, "stngs",
                                                                                              chat=chat_id)))

        await context.bot.answer_callback_query(query.id)
        await query.message.delete()
    except BadRequest as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


async def get_settings(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(None, 1)

    if chat.type != chat.PRIVATE:
        if await is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            await msg.reply_text(text,
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton(text="⚙️ Settings ⚙️",
                                                            url="t.me/{}?start=stngs_{}".format(
                                                                application.bot.username, chat.id))]]))
        else:
            text = "Click here to check your settings."
    else:
        await send_settings(chat.id, user.id, True)


async def donate(update: Update, context):
    user = update.effective_message.from_user
    chat = update.effective_chat

    if chat.type == "private":
        await update.effective_message.reply_text(DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

        if OWNER_ID != 254318997 and DONATION_LINK:
            await update.effective_message.reply_text("You can also donate to the person currently running me "
                                                      "[here]({})".format(DONATION_LINK),
                                                      parse_mode=ParseMode.MARKDOWN)
    else:
        try:
            await context.bot.send_message(user.id, DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            await update.effective_message.reply_text("I've PM'ed you about donating to my creator!")
        except Forbidden:
            await update.effective_message.reply_text("Contact me in PM first to get donation information.")


async def migrate_chats(update: Update, context):
    msg = update.effective_message
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")


async def kcfrsct_fnc(update: Update, context):
    query = update.callback_query
    user = update.effective_user
    _match = re.match(r"rsct_(.*)_33801", query.data)
    if _match:
        try:
            from tg_bot.modules.sql.cust_filters_sql import get_btn_with_di
            _soqka = get_btn_with_di(int(_match.group(1)))
            await context.bot.answer_callback_query(
                query.id,
                text=_soqka.url.replace("\\n", "\n").replace("\\t", "\t"),
                show_alert=True
            )
        except Exception as e:
            print(e)
            await context.bot.answer_callback_query(query.id)


def main():
    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(filters.StatusUpdate.MIGRATE, migrate_chats)

    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(settings_handler)
    application.add_handler(help_callback_handler)
    application.add_handler(settings_callback_handler)
    application.add_handler(migrate_handler)
    application.add_handler(donate_handler)
    application.add_handler(
        CallbackQueryHandler(kcfrsct_fnc, pattern=r"")
    )

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        application.run_webhook(listen="0.0.0.0",
                               port=PORT,
                               url_path=TOKEN,
                               webhook_url=URL + TOKEN)
    else:
        LOGGER.info("Using long polling.")
        application.run_polling(timeout=15)


if __name__ == '__main__':
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    main()
