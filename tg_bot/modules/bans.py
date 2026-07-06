import html
from typing import Optional, List

from telegram import Message, Chat, Update, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, filters
from telegram import InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode

from tg_bot import application, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

RUNBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}



@bot_admin
@can_restrict
@user_admin
@loggable
async def ban(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I really wish I could ban admins...")
        return ""

    if user_id == context.bot.id:
        await message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        await chat.kick_member(user_id)
        await context.bot.send_sticker(chat.id, BAN_STICKER)
        keyboard = []
        reply = "{} ന് ബണ്ണ് കൊടുത്തു വിട്ടിട്ടുണ്ട് !".format(mention_html(member.user.id, member.user.first_name))
        await message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Replied message not found":
            chat_id = update.effective_chat.id
            message = update.effective_message
            reply = "{} ന് ബണ്ണ് കൊടുത്തു വിട്ടിട്ടുണ്ട് !".format(mention_html(member.user.id, member.user.first_name))
            await context.bot.send_message(chat_id, reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            await message.reply_text("Well damn, I can't ban that user.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
async def temp_ban(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I really wish I could ban admins...")
        return ""

    if user_id == context.bot.id:
        await message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return ""

    if not reason:
        await message.reply_text("You haven't specified a time to ban this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        await chat.kick_member(user_id, until_date=bantime)
        await context.bot.send_sticker(chat.id, BAN_STICKER)
        await message.reply_text("Banned! User will be banned for {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            await message.reply_text("Banned! User will be banned for {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            await message.reply_text("Well damn, I can't ban that user.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
async def kick(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if await is_user_ban_protected(chat, user_id):
        await message.reply_text("I really wish I could kick admins...")
        return ""

    if user_id == context.bot.id:
        await message.reply_text("Yeahhh I'm not gonna do that")
        return ""

    res = await chat.unban_member(user_id)
    if res:
        await context.bot.send_sticker(chat.id, BAN_STICKER)
        await message.reply_text("Kicked!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        await message.reply_text("Well damn, I can't kick that user.")

    return ""


@bot_admin
@can_restrict
async def kickme(update: Update, context):
    user_id = update.effective_message.from_user.id
    if await is_user_admin(update.effective_chat, user_id):
        await update.effective_message.reply_text("I wish I could... but you're an admin.")
        return

    res = await update.effective_chat.unban_member(user_id)
    if res:
        await update.effective_message.reply_text("No problem.")
    else:
        await update.effective_message.reply_text("Huh? I can't :/")


@bot_admin
@can_restrict
@user_admin
@loggable
async def unban(update: Update, context, args: List[str] = None) -> str:
    if args is None:
        args = context.args or []
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if user_id == context.bot.id:
        await message.reply_text("How would I unban myself if I wasn't here...?")
        return ""

    if await is_user_in_chat(chat, user_id):
        await message.reply_text("Why are you trying to unban someone that's already in the chat?")
        return ""

    await chat.unban_member(user_id)
    await message.reply_text("Yep, this user can join!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


@bot_admin
async def rban(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await context.bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text("Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.")
            return
        else:
            raise

    if chat.type == 'private':
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not await is_bot_admin(chat, context.bot.id) or not (await chat.get_member(context.bot.id)).can_restrict_members:
        await message.reply_text("I can't restrict people there! Make sure I'm admin and can ban users.")
        return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user")
            return
        else:
            raise

    if await is_user_ban_protected(chat, user_id, member):
        await message.reply_text("I really wish I could ban admins...")
        return

    if user_id == context.bot.id:
        await message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return

    try:
        await chat.kick_member(user_id)
        await message.reply_text("Banned!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            await message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            await message.reply_text("Well damn, I can't ban that user.")

@bot_admin
async def runban(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return
    elif not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await context.bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            await message.reply_text("Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.")
            return
        else:
            raise

    if chat.type == 'private':
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not await is_bot_admin(chat, context.bot.id) or not (await chat.get_member(context.bot.id)).can_restrict_members:
        await message.reply_text("I can't unrestrict people there! Make sure I'm admin and can unban users.")
        return

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user there")
            return
        else:
            raise
            
    if await is_user_in_chat(chat, user_id):
        await message.reply_text("Why are you trying to remotely unban someone that's already in that chat?")
        return

    if user_id == context.bot.id:
        await message.reply_text("I'm not gonna UNBAN myself, I'm an admin there!")
        return

    try:
        await chat.unban_member(user_id)
        await message.reply_text("Yep, this user can join that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            await message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            await message.reply_text("Well damn, I can't unban that user.")


__help__ = """
 - /kickme: kicks the user who issued the command

*Admin only:*
 - /ban <userhandle>: bans a user. (via handle, or reply)
 - /tban <userhandle> x(m/h/d): bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: kicks a user, (via handle, or reply)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, filters=filters.ChatType.GROUPS)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, filters=filters.ChatType.GROUPS)
KICK_HANDLER = CommandHandler("kick", kick, filters=filters.ChatType.GROUPS)
UNBAN_HANDLER = CommandHandler("unban", unban, filters=filters.ChatType.GROUPS)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=filters.ChatType.GROUPS)
RBAN_HANDLER = CommandHandler("rban", rban, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, filters=CustomFilters.sudo_filter)

application.add_handler(BAN_HANDLER)
application.add_handler(TEMPBAN_HANDLER)
application.add_handler(KICK_HANDLER)
application.add_handler(UNBAN_HANDLER)
application.add_handler(KICKME_HANDLER)
application.add_handler(RBAN_HANDLER)
application.add_handler(RUNBAN_HANDLER)
