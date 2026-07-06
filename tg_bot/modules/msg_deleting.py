import html
from typing import Optional, List

from telegram import Message, Chat, Update, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, filters

from tg_bot import application, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_admin, can_delete
from tg_bot.modules.log_channel import loggable


@user_admin
@loggable
async def purge(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    msg = update.effective_message
    if msg.reply_to_message:
        user = update.effective_user
        chat = update.effective_chat
        if await can_delete(chat, context.bot.id):
            message_id = msg.reply_to_message.message_id
            delete_to = msg.message_id - 1
            if args and args[0].isdigit():
                new_del = message_id + int(args[0])
                if new_del < delete_to:
                    delete_to = new_del
            else:
                delete_to = msg.message_id - 1
            for m_id in range(delete_to, message_id - 1, -1):
                try:
                    await context.bot.delete_message(chat.id, m_id)
                except BadRequest as err:
                    if err.message == "Message can't be deleted":
                        await context.bot.send_message(chat.id, "Cannot delete all messages. The messages may be too old, I might "
                                                       "not have delete rights, or this might not be a supergroup.")

                    elif err.message != "Message to delete not found":
                        LOGGER.exception("Error while purging chat messages.")

            try:
                await msg.delete()
            except BadRequest as err:
                if err.message == "Message can't be deleted":
                    await context.bot.send_message(chat.id, "Cannot delete all messages. The messages may be too old, I might "
                                                   "not have delete rights, or this might not be a supergroup.")

                elif err.message != "Message to delete not found":
                    LOGGER.exception("Error while purging chat messages.")

            await context.bot.send_message(chat.id, "Purge complete.")
            return "<b>{}:</b>" \
                   "\n#PURGE" \
                   "\n<b>Admin:</b> {}" \
                   "\nPurged <code>{}</code> messages.".format(html.escape(chat.title),
                                                               mention_html(user.id, user.first_name),
                                                               delete_to - message_id)

    else:
        await msg.reply_text("Reply to a message to select where to start purging from.")

    return ""


@user_admin
@loggable
async def del_message(update: Update, context) -> str:
    if update.effective_message.reply_to_message:
        user = update.effective_user
        chat = update.effective_chat
        if await can_delete(chat, context.bot.id):
            await update.effective_message.reply_to_message.delete()
            await update.effective_message.delete()
            return "<b>{}:</b>" \
                   "\n#DEL" \
                   "\n<b>Admin:</b> {}" \
                   "\nMessage deleted.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))
    else:
        await update.effective_message.reply_text("Whadya want to delete?")

    return ""


__help__ = """
*Admin only:*
 - /del: deletes the message you replied to
 - /purge: deletes all messages between this and the replied to message.
 - /purge <integer X>: deletes the replied message, and X messages following it.
"""

__mod_name__ = "Purges"

DELETE_HANDLER = CommandHandler("del", del_message, filters=filters.ChatType.GROUPS)
PURGE_HANDLER = CommandHandler("purge", purge, filters=filters.ChatType.GROUPS)

application.add_handler(DELETE_HANDLER)
application.add_handler(PURGE_HANDLER)
