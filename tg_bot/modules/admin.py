import html
from typing import Optional, List

from telegram import Message, Chat, Update, User
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, filters, MessageHandler

from tg_bot import application
import tg_bot.modules.sql.setlink_sql as sql
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.string_handling import markdown_parser, mention_html, escape_markdown
from tg_bot.modules.log_channel import loggable


@bot_admin
@can_promote
@user_admin
@loggable
async def promote(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    chat_id = update.effective_chat.id
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = await chat.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        await message.reply_text("How am I meant to promote someone that's already an admin?")
        return ""

    if user_id == context.bot.id:
        await message.reply_text("I can't promote myself! Get an admin to do it for me.")
        return ""

    bot_member = await chat.get_member(context.bot.id)

    await context.bot.promote_chat_member(chat_id, user_id,
                                          can_change_info=bot_member.can_change_info,
                                          can_post_messages=bot_member.can_post_messages,
                                          can_edit_messages=bot_member.can_edit_messages,
                                          can_delete_messages=bot_member.can_delete_messages,
                                          can_restrict_members=bot_member.can_restrict_members,
                                          can_pin_messages=bot_member.can_pin_messages,
                                          can_promote_members=bot_member.can_promote_members)

    await message.reply_text("Successfully promoted!")
    return "<b>{}:</b>" \
           "\n#PROMOTED" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@bot_admin
@can_promote
@user_admin
@loggable
async def demote(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = await chat.get_member(user_id)
    if user_member.status == 'creator':
        await message.reply_text("This person CREATED the chat, how would I demote them?")
        return ""

    if not user_member.status == 'administrator':
        await message.reply_text("Can't demote what wasn't promoted!")
        return ""

    if user_id == context.bot.id:
        await message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return ""

    try:
        await context.bot.promote_chat_member(int(chat.id), int(user_id),
                                              can_change_info=False,
                                              can_post_messages=False,
                                              can_edit_messages=False,
                                              can_delete_messages=False,
                                              can_invite_users=False,
                                              can_restrict_members=False,
                                              can_pin_messages=False,
                                              can_promote_members=False)
        await message.reply_text("Successfully demoted!")
        return "<b>{}:</b>" \
               "\n#DEMOTED" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {}".format(html.escape(chat.title),
                                          mention_html(user.id, user.first_name),
                                          mention_html(user_member.user.id, user_member.user.first_name))

    except BadRequest:
        await message.reply_text("Could not demote. I might not be admin, or the admin status was appointed by another "
                                 "user, so I can't act upon them!")
        return ""


@bot_admin
@can_pin
@user_admin
@loggable
async def pin(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            await context.bot.pin_chat_message(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return "<b>{}:</b>" \
               "\n#PINNED" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""


@bot_admin
@can_pin
@user_admin
@loggable
async def unpin(update: Update, context):
    chat = update.effective_chat
    user = update.effective_user

    try:
        await context.bot.unpin_chat_message(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return "<b>{}:</b>" \
           "\n#UNPINNED" \
           "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))

@bot_admin
@user_admin
async def invite(update: Update, context):
    chat = update.effective_chat
    message = update.effective_message
    
    if chat.username:
        await update.effective_message.reply_text("@{}".format(chat.username))
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = await chat.get_member(context.bot.id)
        if bot_member.can_invite_users:
            invitelink = await context.bot.export_chat_invite_link(chat.id)
            linktext = "Successfully generated new link for *{}:*".format(chat.title)
            link = "`{}`".format(invitelink)
            await message.reply_text(linktext, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            await message.reply_text(link, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        else:
            await message.reply_text("I don't have access to the invite link, try changing my permissions!")
    else:
        await message.reply_text("I can only give you invite links for supergroups and channels, sorry!")

async def link_public(update: Update, context):
    chat = update.effective_chat
    message = update.effective_message
    chat_id = update.effective_chat.id
    invitelink = sql.get_link(chat_id)
    
    if chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        if invitelink:
            await message.reply_text("Link of *{}*:\n`{}`".format(chat.title, invitelink), parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text("The admins of *{}* haven't set link."
                                     " \nLink can be set by following: `/setlink` and get link of chat "
                                     "using /invitelink, paste the link after `/setlink` append.".format(chat.title), parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("I can only can save links for supergroups and channels, sorry!")

@user_admin
async def set_link(update: Update, context):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    chat = update.effective_chat
    raw_text = msg.text
    args = raw_text.split(None, 1)
    
    if len(args) == 2:
        links_text = args[1]

        sql.set_link(chat_id, links_text)
        await msg.reply_text("The link has been set for {}!\nRetrieve link by #link".format((chat.title)))


@user_admin
async def clear_link(update: Update, context):
    chat_id = update.effective_chat.id
    sql.set_link(chat_id, "")
    await update.effective_message.reply_text("Successfully cleared link!")


async def adminlist(update: Update, context):
    administrators = await update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        if user.username:
            name = escape_markdown("@" + user.username)
        text += "\n - {}".format(name)

    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def __stats__():
    return "{} chats have links set.".format(sql.num_chats())

def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        application.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))


__help__ = """
Lazy to promote or demote someone for admins? Want to see basic information about chat? \
All stuff about chatroom such as admin lists, pinning or grabbing an invite link can be \
done easily using the bot.

 - /adminlist: list of admins and members in the chat
 - /staff: same as /adminlist
 - /link: get the group link for this chat.
 - #link: same as /link

*Admin only:*
 - /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifies to users.
 - /unpin: unpins the currently pinned message.
 - /invitelink: generates new invite link.
 - /setlink <your group link here>: set the group link for this chat.
 - /clearlink: clear the group link for this chat.
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to
 
 An example of set a link:
`/setlink https://t.me/joinchat/HwiIk1RADK5gRMr9FBdOrwtae`

An example of promoting someone to admins:
`/promote @username`; this promotes a user to admins.
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler("pin", pin, filters=filters.ChatType.GROUPS)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=filters.ChatType.GROUPS)
LINK_HANDLER = DisableAbleCommandHandler("link", link_public)
SET_LINK_HANDLER = CommandHandler("setlink", set_link, filters=filters.ChatType.GROUPS)
RESET_LINK_HANDLER = CommandHandler("clearlink", clear_link, filters=filters.ChatType.GROUPS)
HASH_LINK_HANDLER = MessageHandler(filters.Regex(r'#link'), link_public)
INVITE_HANDLER = CommandHandler("invitelink", invite, filters=filters.ChatType.GROUPS)
PROMOTE_HANDLER = CommandHandler("promote", promote, filters=filters.ChatType.GROUPS)
DEMOTE_HANDLER = CommandHandler("demote", demote, filters=filters.ChatType.GROUPS)
ADMINLIST_HANDLER = DisableAbleCommandHandler(["adminlist", "staff"], adminlist, filters=filters.ChatType.GROUPS)

application.add_handler(PIN_HANDLER)
application.add_handler(UNPIN_HANDLER)
application.add_handler(INVITE_HANDLER)
application.add_handler(LINK_HANDLER)
application.add_handler(SET_LINK_HANDLER)
application.add_handler(RESET_LINK_HANDLER)
application.add_handler(HASH_LINK_HANDLER)
application.add_handler(PROMOTE_HANDLER)
application.add_handler(DEMOTE_HANDLER)
application.add_handler(ADMINLIST_HANDLER)
