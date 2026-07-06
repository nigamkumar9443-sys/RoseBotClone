import html
from typing import Optional, List

from telegram import Message, Chat, Update, User
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import CommandHandler, filters, MessageHandler

from tg_bot import application, LOGGER
from tg_bot.modules.helper_funcs.chat_status import user_not_admin, user_admin
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import reporting_sql as sql

REPORT_GROUP = 5


@user_admin
async def report_setting(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                await msg.reply_text("Turned on reporting! You'll be notified whenever anyone reports something.")

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                await msg.reply_text("Turned off reporting! You wont get any reports.")
        else:
            await msg.reply_text("Your current report preference is: `{}`".format(sql.user_should_report(chat.id)),
                                 parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                await msg.reply_text("Turned on reporting! Admins who have turned on reports will be notified when /report "
                                     "or @admin are called.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                await msg.reply_text("Turned off reporting! No admins will be notified on /report or @admin.")
        else:
            await msg.reply_text("This chat's current setting is: `{}`".format(sql.chat_should_report(chat.id)),
                                 parse_mode=ParseMode.MARKDOWN)


@user_not_admin
@loggable
async def report(update: Update, context) -> str:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = await chat.get_administrators()

        if chat.username and chat.type == Chat.SUPERGROUP:
            msg = "<b>{}:</b>" \
                  "\n<b>Reported user:</b> {} (<code>{}</code>)" \
                  "\n<b>Reported by:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                      mention_html(
                                                                          reported_user.id,
                                                                          reported_user.first_name),
                                                                      reported_user.id,
                                                                      mention_html(user.id,
                                                                                   user.first_name),
                                                                      user.id)
            link = "\n<b>Link:</b> " \
                   "<a href=\"http://telegram.me/{}/{}\">click here</a>".format(chat.username, message.message_id)

            should_forward = False

        else:
            msg = "{} is calling for admins in \"{}\"!".format(mention_html(user.id, user.first_name),
                                                               html.escape(chat_name))
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    await context.bot.send_message(admin.user.id, msg + link, parse_mode=ParseMode.HTML)

                    if should_forward:
                        await message.reply_to_message.forward(admin.user.id)

                        if len(message.text.split()) > 1:
                            await message.forward(admin.user.id)

                except Forbidden:
                    pass
                except BadRequest as excp:
                    LOGGER.exception("Exception while reporting user")
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is setup to send user reports to admins, via /report and @admin: `{}`".format(
        sql.chat_should_report(chat_id))


def __user_settings__(user_id):
    return "You receive reports from chats you're admin in: `{}`.\nToggle this with /reports in PM.".format(
        sql.user_should_report(user_id))


__mod_name__ = "Reporting"

__help__ = """
 - /report <reason>: reply to a message to report it to admins.
 - @admin: reply to a message to report it to admins.
NOTE: neither of these will get triggered if used by admins

*Admin only:*
 - /reports <on/off>: change report setting, or view current status.
   - If done in pm, toggles your status.
   - If in chat, toggles that chat's status.
"""

REPORT_HANDLER = CommandHandler("report", report, filters=filters.ChatType.GROUPS)
SETTING_HANDLER = CommandHandler("reports", report_setting)
ADMIN_REPORT_HANDLER = MessageHandler(filters.Regex("(?i)@admin(s)?"), report)

application.add_handler(REPORT_HANDLER, REPORT_GROUP)
application.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
application.add_handler(SETTING_HANDLER)
