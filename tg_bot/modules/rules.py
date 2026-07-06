from typing import Optional

from telegram import Message, Update, User
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, filters
from tg_bot.modules.helper_funcs.string_handling import escape_markdown

import tg_bot.modules.sql.rules_sql as sql
from tg_bot import application
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.string_handling import markdown_parser


async def get_rules(update: Update, context):
    chat_id = update.effective_chat.id
    await send_rules(update, chat_id)


async def send_rules(update, chat_id, from_pm=False):
    bot = application.bot
    user = update.effective_user
    try:
        chat = await bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            await bot.send_message(user.id, "The rules shortcut for this chat hasn't been set properly! Ask admins to "
                                            "fix this.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = "The rules for *{}* are:\n\n{}".format(escape_markdown(chat.title), rules)

    if from_pm and rules:
        await bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        await bot.send_message(user.id, "The group admins haven't set any rules for this chat yet. "
                                        "This probably doesn't mean it's lawless though...!")
    elif rules:
        await update.effective_message.reply_text("Contact me in PM to get this group's rules.",
                                                  reply_markup=InlineKeyboardMarkup(
                                                      [[InlineKeyboardButton(text="Rules",
                                                                             url="t.me/{}?start={}".format(bot.username,
                                                                                                           chat_id))]]))
    else:
        await update.effective_message.reply_text("The group admins haven't set any rules for this chat yet. "
                                                  "This probably doesn't mean it's lawless though...!")


@user_admin
async def set_rules(update: Update, context):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 1)
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)
        markdown_rules = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)

        sql.set_rules(chat_id, markdown_rules)
        await update.effective_message.reply_text("Successfully set rules for this group.")


@user_admin
async def clear_rules(update: Update, context):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    await update.effective_message.reply_text("Successfully cleared rules!")


def __stats__():
    return "{} chats have rules set.".format(sql.num_chats())


def __import_data__(chat_id, data):
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat has had it's rules set: `{}`".format(bool(sql.get_rules(chat_id)))


__help__ = """
 - /rules: get the rules for this chat.

*Admin only:*
 - /setrules <your rules here>: set the rules for this chat.
 - /clearrules: clear the rules for this chat.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=filters.ChatType.GROUPS)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=filters.ChatType.GROUPS)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=filters.ChatType.GROUPS)

application.add_handler(GET_RULES_HANDLER)
application.add_handler(SET_RULES_HANDLER)
application.add_handler(RESET_RULES_HANDLER)
