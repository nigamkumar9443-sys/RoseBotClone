from time import sleep

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest, Forbidden
from telegram.ext import CommandHandler, CallbackQueryHandler

import tg_bot.modules.sql.global_bans_sql as gban_sql
import tg_bot.modules.sql.users_sql as user_sql
from tg_bot import application, OWNER_ID


async def get_invalid_chats(update: Update, context, remove: bool = False):
    chat_id = update.effective_chat.id
    chats = user_sql.get_all_chats()
    kicked_chats, progress = 0, 0
    chat_list = []
    progress_message = None

    for chat in chats:

        if ((100 * chats.index(chat)) / len(chats)) > progress:
            progress_bar = f"{progress}% completed in getting invalid chats."
            if progress_message:
                try:
                    await context.bot.edit_message_text(progress_bar, chat_id, progress_message.message_id)
                except:
                    pass
            else:
                progress_message = await context.bot.send_message(chat_id, progress_bar)
            progress += 5

        cid = chat.chat_id
        sleep(0.1)
        try:
            await context.bot.get_chat(cid, timeout=120)
        except (BadRequest, Forbidden):
            kicked_chats += 1
            chat_list.append(cid)
        except:
            pass

    try:
        await progress_message.delete()
    except:
        pass

    if not remove:
        return kicked_chats
    else:
        for muted_chat in chat_list:
            sleep(0.1)
            user_sql.rem_chat(muted_chat)
        return kicked_chats


async def get_invalid_gban(update: Update, context, remove: bool = False):
    banned = gban_sql.get_gban_list()
    ungbanned_users = 0
    ungban_list = []

    for user in banned:
        user_id = user["user_id"]
        sleep(0.1)
        try:
            await context.bot.get_chat(user_id)
        except BadRequest:
            ungbanned_users += 1
            ungban_list.append(user_id)
        except:
            pass

    if not remove:
        return ungbanned_users
    else:
        for user_id in ungban_list:
            sleep(0.1)
            gban_sql.ungban_user(user_id)
        return ungbanned_users

async def dbcleanup(update: Update, context):
    msg = update.effective_message

    await msg.reply_text("Getting invalid chat count ...")
    invalid_chat_count = await get_invalid_chats(update, context)

    await msg.reply_text("Getting invalid gbanned count ...")
    invalid_gban_count = await get_invalid_gban(update, context)

    reply = f"Total invalid chats - {invalid_chat_count}\n"
    reply += f"Total invalid gbanned users - {invalid_gban_count}"

    buttons = [
        [InlineKeyboardButton("Cleanup DB", callback_data=f"db_cleanup")]
    ]

    await update.effective_message.reply_text(reply, reply_markup=InlineKeyboardMarkup(buttons))


async def get_muted_chats(update: Update, context, leave: bool = False):
    chat_id = update.effective_chat.id
    chats = user_sql.get_all_chats()
    muted_chats, progress = 0, 0
    chat_list = []
    progress_message = None

    for chat in chats:

        if ((100 * chats.index(chat)) / len(chats)) > progress:
            progress_bar = f"{progress}% completed in getting muted chats."
            if progress_message:
                try:
                    await context.bot.edit_message_text(progress_bar, chat_id, progress_message.message_id)
                except:
                    pass
            else:
                progress_message = await context.bot.send_message(chat_id, progress_bar)
            progress += 5

        cid = chat.chat_id
        sleep(0.1)

        try:
            await context.bot.send_chat_action(cid, "TYPING", timeout=120)
        except (BadRequest, Forbidden):
            muted_chats += +1
            chat_list.append(cid)
        except:
            pass

    try:
        await progress_message.delete()
    except:
        pass

    if not leave:
        return muted_chats
    else:
        for muted_chat in chat_list:
            sleep(0.1)
            try:
                await context.bot.leave_chat(muted_chat, timeout=120)
            except:
                pass
            user_sql.rem_chat(muted_chat)
        return muted_chats


async def leave_muted_chats(update: Update, context):
    message = update.effective_message
    progress_message = await message.reply_text("Getting chat count ...")
    muted_chats = await get_muted_chats(update, context)

    buttons = [
        [InlineKeyboardButton("Leave chats", callback_data=f"db_leave_chat")]
    ]

    await update.effective_message.reply_text(f"I am muted in {muted_chats} chats.",
                                              reply_markup=InlineKeyboardMarkup(buttons))
    await progress_message.delete()


async def callback_button(update: Update, context):
    query = update.callback_query
    message = query.message
    chat_id = update.effective_chat.id
    query_type = query.data

    admin_list = [OWNER_ID]

    await context.bot.answer_callback_query(query.id)

    if query_type == "db_leave_chat":
        if query.from_user.id in admin_list:
            await context.bot.edit_message_text("Leaving chats ...", chat_id, message.message_id)
            chat_count = await get_muted_chats(update, context, True)
            await context.bot.send_message(chat_id, f"Left {chat_count} chats.")
        else:
            await query.answer("You are not allowed to use this.")
    elif query_type == "db_cleanup":
        if query.from_user.id in admin_list:
            await context.bot.edit_message_text("Cleaning up DB ...", chat_id, message.message_id)
            invalid_chat_count = await get_invalid_chats(update, context, True)
            invalid_gban_count = await get_invalid_gban(update, context, True)
            reply = "Cleaned up {} chats and {} gbanned users from db.".format(invalid_chat_count, invalid_gban_count)
            await context.bot.send_message(chat_id, reply)
        else:
            await query.answer("You are not allowed to use this.")


DB_CLEANUP_HANDLER = CommandHandler("dbcleanup", dbcleanup)
LEAVE_MUTED_CHATS_HANDLER = CommandHandler("leavemutedchats", leave_muted_chats)
BUTTON_HANDLER = CallbackQueryHandler(callback_button, pattern='db_.*')

application.add_handler(DB_CLEANUP_HANDLER)
application.add_handler(LEAVE_MUTED_CHATS_HANDLER)
application.add_handler(BUTTON_HANDLER)

__mod_name__ = "DB Cleanup"
__handlers__ = [DB_CLEANUP_HANDLER, LEAVE_MUTED_CHATS_HANDLER, BUTTON_HANDLER]
