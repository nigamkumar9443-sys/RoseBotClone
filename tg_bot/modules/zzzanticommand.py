import html
from typing import Optional, List

from telegram import Message, Chat, Update, User
from telegram.error import BadRequest
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, filters, MessageHandler
from tg_bot.modules.helper_funcs.string_handling import mention_markdown, mention_html, escape_markdown

import tg_bot.modules.sql.welcome_sql as sql
from tg_bot import application, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, can_delete
from tg_bot.modules.log_channel import loggable


@user_admin
@loggable
async def rem_cmds(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    user = update.effective_user

    if not args:
        del_pref = sql.get_cmd_pref(chat.id)
        if del_pref:
            await update.effective_message.reply_text("I should be deleting `@bluetextbot` messages now.")
        else:
            await update.effective_message.reply_text("I'm currently not deleting `@bluetextbot` messages!")
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_cmd_joined(str(chat.id), True)
        await update.effective_message.reply_text("I'll try to delete `@bluetextbot` messages!")
        return "<b>{}:</b>" \
               "\n#ANTI_COMMAND" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled @AntiCommandBot to <code>ON</code>.".format(html.escape(chat.title),
                                                                          mention_html(user.id, user.first_name))
    elif args[0].lower() in ("off", "no"):
        sql.set_cmd_joined(str(chat.id), False)
        await update.effective_message.reply_text("I won't delete `@bluetextbot`  messages.")
        return "<b>{}:</b>" \
               "\n#ANTI_COMMAND" \
               "\n<b>Admin:</b> {}" \
               "\nHas toggled @AntiCommandBot to <code>OFF</code>.".format(html.escape(chat.title),
                                                                           mention_html(user.id, user.first_name))
    else:
        await update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")
        return ""

async def rem_slash_commands(update: Update, context) -> str:
    chat = update.effective_chat
    msg = update.effective_message
    del_pref = sql.get_cmd_pref(chat.id)

    if del_pref:
        try:
            await msg.delete()
        except BadRequest as excp:
            LOGGER.info(excp)


__help__ = """
I remove messages starting with a /command in groups and supergroups.
- /rmcmd <on/off>: when someone tries to send a @BlueTextBot message, I will try to delete that!
"""

__mod_name__ = "anticommand"

DEL_REM_COMMANDS = CommandHandler("rmcmd", rem_cmds, filters=filters.ChatType.GROUPS)
REM_SLASH_COMMANDS = MessageHandler(filters.COMMAND & filters.ChatType.GROUPS, rem_slash_commands)

application.add_handler(DEL_REM_COMMANDS)
application.add_handler(REM_SLASH_COMMANDS)
