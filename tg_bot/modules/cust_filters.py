from telegram.constants import MessageLimit
MAX_MESSAGE_LENGTH = MessageLimit.MAX_TEXT_LENGTH
import re
from typing import Optional

import telegram
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup, Message, Chat, InlineKeyboardButton
from telegram import Update, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, ApplicationHandlerStop, filters, CallbackQueryHandler
from tg_bot.modules.helper_funcs.string_handling import escape_markdown

from tg_bot import application, LOGGER, BMERNU_SCUT_SRELFTI, SUDO_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.extraction import extract_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import build_keyboard
from tg_bot.modules.helper_funcs.string_handling import split_quotes, button_markdown_parser
from tg_bot.modules.sql import cust_filters_sql as sql

from tg_bot.modules.connection import connected

HANDLER_GROUP = 15
BASIC_FILTER_STRING = "*Filters in this chat:*\n"


async def list_handlers(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = connected(update, context, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = (await application.bot.get_chat(conn)).title
        filter_list = f"*Filters in {chat_name}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local filters"
            filter_list = "*local filters:*\n"
        else:
            chat_name = chat.title
            filter_list = "*Filters in {}*:\n".format(chat_name)

    total_count_f_fliters = sql.num_filters_per_chat(chat_id)
    filter_list += f"**Filter Count**: {total_count_f_fliters}\n"

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        await update.effective_message.reply_text("No filters in {}!".format(chat_name))
        return

    for keyword in all_handlers:
        entry = " - {}\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > MAX_MESSAGE_LENGTH:
            await update.effective_message.reply_text(filter_list, parse_mode=telegram.ParseMode.MARKDOWN)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == BASIC_FILTER_STRING:
        await update.effective_message.reply_text(filter_list, parse_mode=telegram.ParseMode.MARKDOWN)


@user_admin
async def filter_command(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(None, 1)

    conn = connected(update, context, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = (await application.bot.get_chat(conn)).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local filters"
        else:
            chat_name = chat.title

    if len(args) < 2:
        return

    if BMERNU_SCUT_SRELFTI:
        total_fs = sql.num_filters_per_chat(chat_id)
        if total_fs >= BMERNU_SCUT_SRELFTI:
            await msg.reply_text(
                f"You currently have {total_fs} filters. "
                f"The maximum number of filters allowed is {BMERNU_SCUT_SRELFTI}. "
                "You need to delete some filters "
                "Content @Mo_Tech_Group"
                "Bot Update @Mo_Tech_YT"
            )
            return

    extracted = split_quotes(args[1])
    if len(extracted) < 1:
        return
    keyword = extracted[0].lower()

    is_sticker = False
    is_document = False
    is_image = False
    is_voice = False
    is_audio = False
    is_video = False
    media_caption = None
    has_caption = False
    content = None
    buttons = []

    if len(extracted) >= 2:
        offset = len(extracted[1]) - len(msg.text)
        content, buttons = button_markdown_parser(extracted[1], entities=msg.parse_entities(), offset=offset)
        content = content.strip()

    if msg.reply_to_message and msg.reply_to_message.sticker:
        content = msg.reply_to_message.sticker.file_id
        is_sticker = True

    elif msg.reply_to_message and msg.reply_to_message.document:
        offset = len(msg.reply_to_message.caption or "")
        media_caption, buttons = button_markdown_parser(msg.reply_to_message.caption, entities=msg.reply_to_message.parse_entities(), offset=offset)
        content = msg.reply_to_message.document.file_id
        is_document = True
        has_caption = True

    elif msg.reply_to_message and msg.reply_to_message.photo:
        offset = len(msg.reply_to_message.caption or "")
        media_caption, buttons = button_markdown_parser(msg.reply_to_message.caption, entities=msg.reply_to_message.parse_entities(), offset=offset)
        content = msg.reply_to_message.photo[-1].file_id
        is_image = True
        has_caption = True

    elif msg.reply_to_message and msg.reply_to_message.audio:
        offset = len(msg.reply_to_message.caption or "")
        media_caption, buttons = button_markdown_parser(msg.reply_to_message.caption, entities=msg.reply_to_message.parse_entities(), offset=offset)
        content = msg.reply_to_message.audio.file_id
        is_audio = True
        has_caption = True

    elif msg.reply_to_message and msg.reply_to_message.voice:
        offset = len(msg.reply_to_message.caption or "")
        media_caption, buttons = button_markdown_parser(msg.reply_to_message.caption, entities=msg.reply_to_message.parse_entities(), offset=offset)
        content = msg.reply_to_message.voice.file_id
        is_voice = True
        has_caption = True

    elif msg.reply_to_message and msg.reply_to_message.video:
        offset = len(msg.reply_to_message.caption or "")
        media_caption, buttons = button_markdown_parser(msg.reply_to_message.caption, entities=msg.reply_to_message.parse_entities(), offset=offset)
        content = msg.reply_to_message.video.file_id
        is_video = True
        has_caption = True

    elif msg.reply_to_message and msg.reply_to_message.text:
        content = msg.reply_to_message.text

    elif not content:
        await msg.reply_text("There is no note message - You can't JUST have buttons, you need a message to go with it!")
        return

    for handler in application.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            application.remove_handler(handler, HANDLER_GROUP)

    sql.add_filter(chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                   buttons, media_caption, has_caption)

    await msg.reply_text("Handler '{}' added in *{}*!".format(keyword, chat_name), parse_mode=telegram.ParseMode.MARKDOWN)
    raise ApplicationHandlerStop


@user_admin
async def stop_filter(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    conn = connected(update, context, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = (await application.bot.get_chat(conn)).title
    else:
        chat_id = chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    if len(args) < 2:
        return

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        await update.effective_message.reply_text("No filters are active here!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat_id, args[1])
            await update.effective_message.reply_text("Yep, I'll stop replying to that in *{}*.".format(chat_name), parse_mode=telegram.ParseMode.MARKDOWN)
            raise ApplicationHandlerStop

    await update.effective_message.reply_text("That's not a current filter - run /filters for all active filters.")


async def reply_filter(update: Update, context):
    chat = update.effective_chat
    message = update.effective_message
    to_match = extract_text(message)
    if not to_match:
        return

    if message.reply_to_message:
        message = message.reply_to_message


    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            filt = sql.get_filter(chat.id, keyword)
            buttons = sql.get_buttons(chat.id, filt.keyword)
            media_caption = filt.caption if filt.caption is not None else ""
            keyboard = None
            if len(buttons) > 0:
                keyboard = InlineKeyboardMarkup(build_keyboard(buttons))
            if filt.is_sticker:
                await message.reply_sticker(filt.reply, reply_markup=keyboard)
            elif filt.is_document:
                await message.reply_document(filt.reply, caption=media_caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            elif filt.is_image:
                await message.reply_photo(filt.reply, caption=media_caption, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
            elif filt.is_audio:
                await message.reply_audio(filt.reply, caption=media_caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            elif filt.is_voice:
                await message.reply_voice(filt.reply, caption=media_caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            elif filt.is_video:
                await message.reply_video(filt.reply, caption=media_caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            elif filt.has_markdown:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                should_preview_disabled = True
                if "telegra.ph" in filt.reply or "youtu.be" in filt.reply:
                    should_preview_disabled = False

                try:
                    await message.reply_text(filt.reply, parse_mode=ParseMode.MARKDOWN,
                                             disable_web_page_preview=should_preview_disabled,
                                             reply_markup=keyboard)
                except BadRequest as excp:
                    if excp.message == "Unsupported url protocol":
                        await message.reply_text("You seem to be trying to use an unsupported url protocol. Telegram "
                                                 "doesn't support buttons for some protocols, such as tg://. Please try "
                                                 "again, or ask in @KeralaBots for help.")
                    elif excp.message == "Replied message not found":
                        await context.bot.send_message(chat.id, filt.reply, parse_mode=ParseMode.MARKDOWN,
                                               disable_web_page_preview=True,
                                               reply_markup=keyboard)
                    else:
                        await message.reply_text("This note could not be sent, as it is incorrectly formatted. Ask in "
                                                 "@KeralaBots if you can't figure out why!")
                        LOGGER.warning("Message %s could not be parsed", str(filt.reply))
                        LOGGER.exception("Could not parse filter %s in chat %s", str(filt.keyword), str(chat.id))

            else:
                await message.reply_text(filt.reply)
            break

async def rmall_filters(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        await update.effective_message.reply_text(
            "Only the chat owner can clear all notes at once.")
    else:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton(text="Stop all filters", callback_data="filters_rmall")], [
                                       InlineKeyboardButton(text="Cancel", callback_data="filters_cancel")]])
        await update.effective_message.reply_text(
            f"Are you sure you would like to stop ALL filters in {chat.title}? This action cannot be undone.", reply_markup=buttons, parse_mode=ParseMode.MARKDOWN)


async def rmall_callback(update: Update, context):
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = await chat.get_member(query.from_user.id)
    if query.data == 'filters_rmall':
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            allfilters = sql.get_chat_triggers(chat.id)
            if not allfilters:
                await msg.edit_text("No filters in this chat, nothing to stop!")
                return

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)

            for i in filterlist:
                sql.remove_filter(chat.id, i)

            await msg.edit_text(f"Cleaned {count} filters in {chat.title}")

        if member.status == "administrator":
            await query.answer(
                "Only owner of the chat can do this.")

        if member.status == "member":
            await query.answer(
                "You need to be admin to do this.")
    elif query.data == 'filters_cancel':
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            await msg.edit_text("Clearing of all filters has been cancelled.")
            return
        if member.status == "administrator":
            await query.answer(
                "Only owner of the chat can do this.")
        if member.status == "member":
            await query.answer(
                "You need to be admin to do this.")


def __stats__():
    return "{} filters, across {} chats.".format(sql.num_filters(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "There are `{}` custom filters here.".format(len(cust_filters))


__help__ = """
 - /filters: list all active filters in this chat.

*Admin only:*
 - /filter <keyword> <reply message>: add a filter to this chat. The bot will now reply that message whenever 'keyword'\
is mentioned. If you reply to a sticker with a keyword, the bot will reply with that sticker. NOTE: all filter \
keywords are in lowercase. If you want your keyword to be a sentence, use quotes. eg: /filter "hey there" How you \
doin?
 - /stop <filter keyword>: stop that filter.
*Chat creator only:*
 - /removeallfilters: Stop all filters in chat at once (Limited to creators only).

"""

__mod_name__ = "Filters"

FILTER_HANDLER = CommandHandler("filter", filter_command)
STOP_HANDLER = CommandHandler("stop", stop_filter)
RMALLFILTER_HANDLER = CommandHandler("removeallfilters", rmall_filters, filters=filters.ChatType.GROUPS)
RMALLFILTER_CALLBACK = CallbackQueryHandler(rmall_callback, pattern=r"filters_.*")
LIST_HANDLER = DisableAbleCommandHandler("filters", list_handlers, admin_ok=True)
CUST_FILTER_HANDLER = MessageHandler(CustomFilters.has_text, reply_filter)

application.add_handler(FILTER_HANDLER)
application.add_handler(STOP_HANDLER)
application.add_handler(RMALLFILTER_HANDLER)
application.add_handler(RMALLFILTER_CALLBACK)
application.add_handler(LIST_HANDLER)
application.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
