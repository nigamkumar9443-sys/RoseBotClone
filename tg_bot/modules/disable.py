from typing import Union, List, Optional

from future.utils import string_types
from telegram.constants import ParseMode
from telegram import Update, Bot, Chat, User
from telegram.ext import CommandHandler, filters, MessageHandler
from tg_bot.modules.helper_funcs.string_handling import escape_markdown

from tg_bot import application, SUDO_USERS
from tg_bot.modules.helper_funcs.handlers import CMD_STARTERS
from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from tg_bot.modules.helper_funcs.chat_status import user_admin
    from telegram import Update

    from tg_bot.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):
        def __init__(self, command, callback, admin_ok=False, **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            chat = update.effective_chat
            user = update.effective_user
            if super().check_update(update):
                command = update.effective_message.text_html.split(None, 1)[0][1:].split('@')[0]

                if sql.is_command_disabled(chat.id, command):
                    if user and user.id in [777000, 20516707, 7351948, 1087968824]:
                        return True
                    if chat.type == 'private' or (user and user.id in SUDO_USERS):
                        return True
                    return command in ADMIN_CMDS

                else:
                    return True

            return False


    class DisableAbleRegexHandler(MessageHandler):
        def __init__(self, pattern, callback, friendly="", **kwargs):
            super().__init__(filters.Regex(pattern), callback, **kwargs)
            DISABLE_OTHER.append(friendly or pattern)
            self.friendly = friendly or pattern

        def check_update(self, update):
            chat = update.effective_chat
            return super().check_update(update) and not sql.is_command_disabled(chat.id, self.friendly)


    @user_admin
    async def disable(update: Update, context, args: List[str] = None):
        if args is None:
            args = context.args or []
        chat = update.effective_chat
        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, disable_cmd)
                await update.effective_message.reply_text("Disabled the use of `{}`".format(disable_cmd),
                                                          parse_mode=ParseMode.MARKDOWN)
            else:
                await update.effective_message.reply_text("That command can't be disabled")

        else:
            await update.effective_message.reply_text("What should I disable?")


    @user_admin
    async def enable(update: Update, context, args: List[str] = None):
        if args is None:
            args = context.args or []
        chat = update.effective_chat
        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                await update.effective_message.reply_text("Enabled the use of `{}`".format(enable_cmd),
                                                          parse_mode=ParseMode.MARKDOWN)
            else:
                await update.effective_message.reply_text("Is that even disabled?")

        else:
            await update.effective_message.reply_text("What should I enable?")


    @user_admin
    async def list_cmds(update: Update, context):
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += " - `{}`\n".format(escape_markdown(cmd))
            await update.effective_message.reply_text("The following commands are toggleable:\n{}".format(result),
                                                      parse_mode=ParseMode.MARKDOWN)
        else:
            await update.effective_message.reply_text("No commands can be disabled.")


    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "No commands are disabled!"

        result = ""
        for cmd in disabled:
            result += " - `{}`\n".format(escape_markdown(cmd))
        return "The following commands are currently restricted:\n{}".format(result)


    async def commands(update: Update, context):
        chat = update.effective_chat
        await update.effective_message.reply_text(build_curr_disabled(chat.id), parse_mode=ParseMode.MARKDOWN)


    def __stats__():
        return "{} disabled items, across {} chats.".format(sql.num_disabled(), sql.num_chats())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        return build_curr_disabled(chat_id)


    __mod_name__ = "Disable"

    __help__ = """
 - /cmds: check the current status of disabled commands

*Admin only:*
 - /enable <cmd name>: enable that command
 - /disable <cmd name>: disable that command
 - /listcmds: list all possible toggleable commands
    """

    DISABLE_HANDLER = CommandHandler("disable", disable, filters=filters.ChatType.GROUPS)
    ENABLE_HANDLER = CommandHandler("enable", enable, filters=filters.ChatType.GROUPS)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands, filters=filters.ChatType.GROUPS)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds, filters=filters.ChatType.GROUPS)

    application.add_handler(DISABLE_HANDLER)
    application.add_handler(ENABLE_HANDLER)
    application.add_handler(COMMANDS_HANDLER)
    application.add_handler(TOGGLE_HANDLER)

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleRegexHandler = MessageHandler
