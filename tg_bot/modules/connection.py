from typing import Optional, List

from telegram.constants import ParseMode
from telegram import Message, Chat, Update, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, filters

import tg_bot.modules.sql.connection_sql as sql
from tg_bot import application, LOGGER, SUDO_USERS
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time

from tg_bot.modules.keyboard import keyboard

@user_admin
async def allow_connections(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            print(var)
            if (var == "no"):
                sql.set_allow_connect_to_chat(chat.id, False)
                await update.effective_message.reply_text("Disabled connections to this chat for users")
            elif(var == "yes"):
                sql.set_allow_connect_to_chat(chat.id, True)
                await update.effective_message.reply_text("Enabled connections to this chat for users")
            else:
                await update.effective_message.reply_text("Please enter on/yes/off/no in group!")
        else:
            await update.effective_message.reply_text("Please enter on/yes/off/no in group!")
    else:
        await update.effective_message.reply_text("Please enter on/yes/off/no in group!")


async def connect_chat(update: Update, context, args):
    chat = update.effective_chat
    user = update.effective_user
    if update.effective_chat.type == 'private':
        if len(args) >= 1:
            try:
                connect_chat = int(args[0])
            except ValueError:
                await update.effective_message.reply_text("Invalid Chat ID provided!")
            if ((await context.bot.get_chat_member(connect_chat, update.effective_message.from_user.id)).status in ('administrator', 'creator') or 
                                     (sql.allow_connect_to_chat(connect_chat) == True) and 
                                     (await context.bot.get_chat_member(connect_chat, update.effective_message.from_user.id)).status in ('member')) or (
                                     user.id in SUDO_USERS):

                connection_status = sql.connect(update.effective_message.from_user.id, connect_chat)
                if connection_status:
                    chat_name = (await application.bot.get_chat(connected(update, context, chat, user.id, need_admin=False))).title
                    await update.effective_message.reply_text("Successfully connected to *{}*".format(chat_name), parse_mode=ParseMode.MARKDOWN)

                    history = sql.get_history(user.id)
                    if history:
                        if history.chat_id1:
                            history1 = int(history.chat_id1)
                        if history.chat_id2:
                            history2 = int(history.chat_id2)
                        if history.chat_id3:
                            history3 = int(history.chat_id3)
                        if history.updated:
                            number = history.updated

                        if number == 1 and connect_chat != history2 and connect_chat != history3:
                            history1 = connect_chat
                            number = 2
                        elif number == 2 and connect_chat != history1 and connect_chat != history3:
                            history2 = connect_chat
                            number = 3
                        elif number >= 3 and connect_chat != history2 and connect_chat != history1:
                            history3 = connect_chat
                            number = 1
                        else:
                            print("Error")
                    
                        print(history.updated)
                        print(number)

                        sql.add_history(user.id, history1, history2, history3, number)
                        print(history.user_id, history.chat_id1, history.chat_id2, history.chat_id3, history.updated)
                    else:
                        sql.add_history(user.id, connect_chat, "0", "0", 2)
                    await keyboard(update, context)
                    
                else:
                    await update.effective_message.reply_text("Connection failed!")
            else:
                await update.effective_message.reply_text("Connections to this chat not allowed!")
        else:
            await update.effective_message.reply_text("Input chat ID to connect!")
            history = sql.get_history(user.id)
            print(history.user_id, history.chat_id1, history.chat_id2, history.chat_id3, history.updated)

    else:
        await update.effective_message.reply_text("Usage limited to PMs only!")


async def disconnect_chat(update: Update, context):
    if update.effective_chat.type == 'private':
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = await update.effective_message.reply_text("Disconnected from chat!")
            await keyboard(update, context)
        else:
           await update.effective_message.reply_text("Disconnection unsuccessfull!")
    else:
        await update.effective_message.reply_text("Usage restricted to PMs only")


def connected(update: Update, context, chat, user_id, need_admin=True):
    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):
        conn_id = sql.get_connected_chat(user_id).chat_id
        if (context.bot.get_chat_member(conn_id, user_id).status in ('administrator', 'creator') or 
                                     (sql.allow_connect_to_chat(conn_id) == True) and 
                                     context.bot.get_chat_member(conn_id, update.effective_message.from_user.id).status in ('member')) or (
                                     user_id in SUDO_USERS):
            if need_admin == True:
                if context.bot.get_chat_member(conn_id, update.effective_message.from_user.id).status in ('administrator', 'creator') or user_id in SUDO_USERS:
                    return conn_id
                else:
                    update.effective_message.reply_text("You need to be a admin in a connected group!")
                    exit(1)
            else:
                return conn_id
        else:
            update.effective_message.reply_text("Group changed rights connection or you are not admin anymore.\nI'll disconnect you.")
            disconnect_chat(update, context)
            exit(1)
    else:
        return False



__help__ = """
Actions are available with connected groups:
 • View and edit notes
 • View and edit filters
 • More in future!

 - /connect <chatid>: Connect to remote chat
 - /disconnect: Disconnect from chat
 - /allowconnect on/yes/off/no: Allow connect users to group
"""

__mod_name__ = "Connections"

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat)
ALLOW_CONNECTIONS_HANDLER = CommandHandler("allowconnect", allow_connections)

application.add_handler(CONNECT_CHAT_HANDLER)
application.add_handler(DISCONNECT_CHAT_HANDLER)
application.add_handler(ALLOW_CONNECTIONS_HANDLER)
