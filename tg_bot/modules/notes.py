import re
from io import BytesIO
from typing import Optional, List

from telegram.constants import MessageLimit
MAX_MESSAGE_LENGTH = MessageLimit.MAX_TEXT_LENGTH
from telegram.constants import ParseMode
from telegram import Message, Update, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import CommandHandler, filters, MessageHandler
from tg_bot.modules.helper_funcs.string_handling import escape_markdown

import tg_bot.modules.sql.notes_sql as sql
from tg_bot import application, MESSAGE_DUMP, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from tg_bot.modules.helper_funcs.msg_types import get_note_type

from tg_bot.modules.connection import connected

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")

_ENUM_FUNC_MAP = {}

def _get_enum_func(msg_type):
    if not _ENUM_FUNC_MAP:
        _bot = application.bot
        _ENUM_FUNC_MAP[sql.Types.TEXT.value] = _bot.send_message
        _ENUM_FUNC_MAP[sql.Types.BUTTON_TEXT.value] = _bot.send_message
        _ENUM_FUNC_MAP[sql.Types.STICKER.value] = _bot.send_sticker
        _ENUM_FUNC_MAP[sql.Types.DOCUMENT.value] = _bot.send_document
        _ENUM_FUNC_MAP[sql.Types.PHOTO.value] = _bot.send_photo
        _ENUM_FUNC_MAP[sql.Types.AUDIO.value] = _bot.send_audio
        _ENUM_FUNC_MAP[sql.Types.VOICE.value] = _bot.send_voice
        _ENUM_FUNC_MAP[sql.Types.VIDEO.value] = _bot.send_video
    return _ENUM_FUNC_MAP[msg_type]


async def get(update: Update, context, notename, show_none=True, no_format=False):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(update, context, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        send_id = user.id
    else:
        chat_id = update.effective_chat.id
        send_id = chat_id

    note = sql.get_note(chat_id, notename)
    message = update.effective_message

    if note:
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=MESSAGE_DUMP, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        await message.reply_text("This message seems to have been lost - I'll remove it "
                                                 "from your notes list.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=chat_id, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        await message.reply_text("Looks like the original sender of this note has deleted "
                                                 "their message - sorry! Get your bot admin to start using a "
                                                 "message dump to avoid this. I'll remove this note from "
                                                 "your saved notes.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            text = note.value
            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            should_preview_disabled = True
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)
                if "telegra.ph" in text or "youtu.be" in text:
                    should_preview_disabled = False

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):

                    await context.bot.send_message(chat_id, text, reply_to_message_id=reply_id,
                                                   parse_mode=parseMode, disable_web_page_preview=should_preview_disabled,
                                                   reply_markup=keyboard)
                else:
                    await _get_enum_func(note.msgtype)(chat_id, note.file, caption=text, reply_to_message_id=reply_id,
                                                      parse_mode=parseMode, disable_web_page_preview=should_preview_disabled,
                                                      reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    await message.reply_text("Looks like you tried to mention someone I've never seen before. If you really "
                                             "want to mention them, forward one of their messages to me, and I'll be able "
                                             "to tag them!")
                elif FILE_MATCHER.match(note.value):
                    await message.reply_text("This note was an incorrectly imported file from another bot - I can't use "
                                             "it. If you really need it, you'll have to save it again. In "
                                             "the meantime, I'll remove it from your notes list.")
                    sql.rm_note(chat_id, notename)
                else:
                    await message.reply_text("This note could not be sent, as it is incorrectly formatted. Ask in "
                                             "@MarieSupport if you can't figure out why!")
                    LOGGER.exception("Could not parse message #%s in chat %s", notename, str(chat_id))
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        await message.reply_text("This note doesn't exist")


async def cmd_get(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    if len(args) >= 2 and args[1].lower() == "noformat":
        await get(update, context, args[0], show_none=True, no_format=True)
    elif len(args) >= 1:
        await get(update, context, args[0], show_none=True)
    else:
        await update.effective_message.reply_text("Get rekt")


async def hash_get(update: Update, context):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    await get(update, context, no_hash, show_none=False)


@user_admin
async def save(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(update, context, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = (await application.bot.get_chat(conn)).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    msg = update.effective_message

    note_name, text, data_type, content, buttons = get_note_type(msg)

    if data_type is None:
        await msg.reply_text("Dude, there's no note")
        return


    if len(text.strip()) == 0:
        text = note_name

    sql.add_note_to_db(chat_id, note_name, text, data_type, buttons=buttons, file=content)

    await msg.reply_text(
        "OK, Added {note_name} in *{chat_name}*.\nGet it with /get {note_name}, or #{note_name}".format(note_name=note_name, chat_name=chat_name), parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            await msg.reply_text("Seems like you're trying to save a message from a bot. Unfortunately, "
                                 "bots can't forward bot messages, so I can't save the exact message. "
                                 "\nI'll save all the text I can, but if you want more, you'll have to "
                                 "forward the message yourself, and then save it.")
        else:
            await msg.reply_text("Bots are kinda handicapped by telegram, making it hard for bots to "
                                 "interact with other bots, so I can't save this message "
                                 "like I usually would - do you mind forwarding it and "
                                 "then saving that new message? Thanks!")
        return


@user_admin
async def clear(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(update, context, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = (await application.bot.get_chat(conn)).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    if len(args) >= 1:
        notename = args[0]

        if sql.rm_note(chat_id, notename):
            await update.effective_message.reply_text("Successfully removed note.")
        else:
            await update.effective_message.reply_text("That's not a note in my database!")


async def list_notes(update: Update, context):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(update, context, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = (await application.bot.get_chat(conn)).title
        msg = "*Notes in {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = ""
            msg = "*Local Notes:*\n"
        else:
            chat_name = chat.title
            msg = "*Notes in {}:*\n"

    note_list = sql.get_all_chat_notes(chat_id)

    for note in note_list:
        note_name = escape_markdown(" - {}\n".format(note.name))
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if msg == "*Notes in chat:*\n":
        await update.effective_message.reply_text("No notes in this chat!")

    elif len(msg) != 0:
        await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get('extra', {}).items():
        match = FILE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            application.bot.send_document(chat_id, document=output, filename="failed_imports.txt",
                                         caption="These files/photos failed to import due to originating "
                                                 "from another bot. This is a telegram API restriction, and can't "
                                                 "be avoided. Sorry for the inconvenience!")


def __stats__():
    return "{} notes, across {} chats.".format(sql.num_notes(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return "There are `{}` notes in this chat.".format(len(notes))


__help__ = """
 - /get <notename>: get the note with this notename
 - #<notename>: same as /get
 - /notes or /saved: list all saved notes in this chat

If you would like to retrieve the contents of a note without any formatting, use `/get <notename> noformat`. This can \
be useful when updating a current note.

*Admin only:*
 - /save <notename> <notedata>: saves notedata as a note with name notename
A button can be added to a note by using standard markdown link syntax - the link should just be prepended with a \
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`. Check /markdownhelp for more info.
 - /save <notename>: save the replied message as a note with name notename
 - /clear <notename>: clear note with this name
"""

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get", cmd_get)
HASH_GET_HANDLER = MessageHandler(filters.Regex(r"^#[^\s]+"), hash_get)

SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"], list_notes, admin_ok=True)

application.add_handler(GET_HANDLER)
application.add_handler(SAVE_HANDLER)
application.add_handler(LIST_HANDLER)
application.add_handler(DELETE_HANDLER)
application.add_handler(HASH_GET_HANDLER)
