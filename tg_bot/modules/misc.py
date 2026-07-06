import html
import json
import random
from datetime import datetime
from typing import Optional, List

import requests
from telegram import Message, Chat, Update, MessageEntity
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, filters
from telegram.helpers import mention_html

from tg_bot import application, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER
from tg_bot.__main__ import GDPR
from tg_bot.__main__ import STATS, USER_INFO
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters

RUN_STRINGS = (
    "Where do you think you're going?",
    "Huh? what? did they get away?",
    "ZZzzZZzz... Huh? what? oh, just them again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear that's fun.",
    "Go bother someone else, no-one here cares.",
    "You can run, but you can't hide.",
    "Is that all you've got?",
    "I'm behind you...",
    "You've got company!",
    "We can do this the easy way, or the hard way.",
    "You just don't get it, do you?",
    "Yeah, you better run!",
    "Please, remind me how much I care?",
    "I'd run faster if I were you.",
    "That's definitely the droid we're looking for.",
    "May the odds be ever in your favour.",
    "Famous last words.",
    "And they disappeared forever, never to be seen again.",
    "\"Oh, look at me! I'm so cool, I can run from a bot!\" - this person",
    "Yeah yeah, just tap /kickme already.",
    "Here, take this ring and head to Mordor while you're at it.",
    "Legend has it, they're still running...",
    "Unlike Harry Potter, your parents can't protect you from me.",
    "Fear leads to anger. Anger leads to hate. Hate leads to suffering. If you keep running in fear, you might "
    "be the next Vader.",
    "Multiple calculations later, I have decided my interest in your shenanigans is exactly 0.",
    "Legend has it, they're still running.",
    "Keep it up, not sure we want you here anyway.",
    "You're a wiza- Oh. Wait. You're not Harry, keep moving.",
    "NO RUNNING IN THE HALLWAYS!",
    "Hasta la vista, baby.",
    "Who let the dogs out?",
    "It's funny, because no one cares.",
    "Ah, what a waste. I liked that one.",
    "Frankly, my dear, I don't give a damn.",
    "My milkshake brings all the boys to yard... So run faster!",
    "You can't HANDLE the truth!",
    "A long time ago, in a galaxy far far away... Someone would've cared about that. Not anymore though.",
    "Hey, look at them! They're running from the inevitable banhammer... Cute.",
    "Han shot first. So will I.",
    "What are you running after, a white rabbit?",
    "As The Doctor would say... RUN!",
)

SLAP_TEMPLATES = (
    "{user1} {hits} {user2} with a {item}.",
    "{user1} {hits} {user2} in the face with a {item}.",
    "{user1} {hits} {user2} around a bit with a {item}.",
    "{user1} {throws} a {item} at {user2}.",
    "{user1} grabs a {item} and {throws} it at {user2}'s face.",
    "{user1} launches a {item} in {user2}'s general direction.",
    "{user1} starts slapping {user2} silly with a {item}.",
    "{user1} pins {user2} down and repeatedly {hits} them with a {item}.",
    "{user1} grabs up a {item} and {hits} {user2} with it.",
    "{user1} ties {user2} to a chair and {throws} a {item} at them.",
    "{user1} gave a friendly push to help {user2} learn to swim in lava."
)

ITEMS = (
    "cast iron skillet",
    "large trout",
    "baseball bat",
    "cricket bat",
    "wooden cane",
    "nail",
    "printer",
    "shovel",
    "CRT monitor",
    "physics textbook",
    "toaster",
    "portrait of Richard Stallman",
    "television",
    "five ton truck",
    "roll of duct tape",
    "book",
    "laptop",
    "old television",
    "sack of rocks",
    "rainbow trout",
    "rubber chicken",
    "spiked bat",
    "fire extinguisher",
    "heavy rock",
    "chunk of dirt",
    "beehive",
    "piece of rotten meat",
    "bear",
    "ton of bricks",
)

THROW = (
    "throws",
    "flings",
    "chucks",
    "hurls",
)

HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks",
    "bashes",
)

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"
GMAPS_TIME = "https://maps.googleapis.com/maps/api/timezone/json"


async def runs(update: Update, context):
    await update.effective_message.reply_text(random.choice(RUN_STRINGS))


async def slap(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    msg = update.effective_message

    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = await context.bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    else:
        user1 = "[{}](tg://user?id={})".format(context.bot.first_name, context.bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    await reply_text(repl, parse_mode=ParseMode.MARKDOWN)


async def get_bot_ip(update: Update, context):
    res = requests.get("http://ipinfo.io/ip")
    await update.message.reply_text(res.text)


async def get_id(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            await update.effective_message.reply_text(
                "The original sender, {}, has an ID of `{}`.\nThe forwarder, {}, has an ID of `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id),
                parse_mode=ParseMode.MARKDOWN)
        else:
            user = await context.bot.get_chat(user_id)
            await update.effective_message.reply_text("{}'s id is `{}`.".format(escape_markdown(user.first_name), user.id),
                                                      parse_mode=ParseMode.MARKDOWN)
    else:
        chat = update.effective_chat
        if chat.type == "private":
            await update.effective_message.reply_text("Your id is `{}`.".format(chat.id),
                                                      parse_mode=ParseMode.MARKDOWN)

        else:
            await update.effective_message.reply_text("This group's id is `{}`.".format(chat.id),
                                                      parse_mode=ParseMode.MARKDOWN)


async def info(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    msg = update.effective_message
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = await context.bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        await msg.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = "<b>User info</b>:" \
           "\nID: <code>{}</code>" \
           "\nFirst Name: {}".format(user.id, html.escape(user.first_name))

    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))

    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))

    text += "\nPermanent user link: {}".format(mention_html(user.id, "link"))

    if user.id == OWNER_ID:
        text += "\n\nThis person is my owner - I would never do anything against them!"
    else:
        if user.id in SUDO_USERS:
            text += "\nThis person is one of my sudo users! " \
                    "Nearly as powerful as my owner - so watch it."
        else:
            if user.id in SUPPORT_USERS:
                text += "\nThis person is one of my support users! " \
                        "Not quite a sudo user, but can still gban you off the map."

            if user.id in WHITELIST_USERS:
                text += "\nThis person has been whitelisted! " \
                        "That means I'm not allowed to ban/kick them."

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def get_time(update: Update, context, args: List[str] = None):
    if args is None:
        args = context.args or []
    location = " ".join(args)
    if location.lower() == context.bot.first_name.lower():
        await update.effective_message.reply_text("Its always banhammer time for me!")
        await context.bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location))

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(GMAPS_TIME, params=dict(location="{},{}".format(lat, long), timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp + offset).strftime("%H:%M:%S on %A %d %B")
                await update.message.reply_text("It's {} in {}".format(time_there, location))


async def echo(update: Update, context):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        await message.reply_to_message.reply_text(args[1])
    else:
        await message.reply_text(args[1], quote=False)
    await message.delete()


async def gdpr(update: Update, context):
    await update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    await update.effective_message.reply_text("Your personal data has been deleted.\n\nNote that this will not unban "
                                              "you from any chats, as that is telegram data, not Marie data. "
                                              "Flooding, warns, and gbans are also preserved, as of "
                                              "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
                                              "which clearly states that the right to erasure does not apply "
                                              "\"for the performance of a task carried out in the public interest\", as is "
                                              "the case for the aforementioned pieces of data.",
                                              parse_mode=ParseMode.MARKDOWN)


MARKDOWN_HELP = """
Markdown is a very powerful formatting tool supported by telegram. {} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
""".format("the bot")


async def markdown_help(update: Update, context):
    await update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text("Try forwarding the following message to me, and you'll see!")
    await update.effective_message.reply_text("/save test This is a markdown test. _italics_, *bold*, `code`, "
                                              "[URL](example.com) [button](buttonurl:github.com) "
                                              "[button2](buttonurl://google.com:same)")


async def stats(update: Update, context):
    await update.effective_message.reply_text("Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS]))

async def stickerid(update: Update, context):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        await update.effective_message.reply_text("Hello " +
                                                  "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)
                                                  + ", The sticker id you are replying is :\n```" + 
                                                  escape_markdown(msg.reply_to_message.sticker.file_id) + "```",
                                                  parse_mode=ParseMode.MARKDOWN)
    else:
        await update.effective_message.reply_text("Hello " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                                  msg.from_user.id) + ", Please reply to sticker message to get id sticker",
                                                  parse_mode=ParseMode.MARKDOWN)
async def getsticker(update: Update, context):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        await context.bot.send_chat_action(chat_id, "typing")
        await update.effective_message.reply_text("Hello " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                                  msg.from_user.id) + ", Please check the file you requested below."
                                                  "\nPlease use this feature wisely!",
                                                  parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_chat_action(chat_id, "upload_document")
        file_id = msg.reply_to_message.sticker.file_id
        newFile = await context.bot.get_file(file_id)
        newFile.download('sticker.png')
        await context.bot.send_document(chat_id, document=open('sticker.png', 'rb'))
        await context.bot.send_chat_action(chat_id, "upload_photo")
        await context.bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))
        
    else:
        await context.bot.send_chat_action(chat_id, "typing")
        await update.effective_message.reply_text("Hello " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                                  msg.from_user.id) + ", Please reply to sticker message to get sticker image",
                                                  parse_mode=ParseMode.MARKDOWN)

__help__ = """
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /runs: reply a random string from an array of replies.
 - /slap: slap a user, or get slapped if not a reply.
 - /time <place>: gives the local time at the given place.
 - /info: get information about a user.
 - /gdpr: deletes your information from the bot's database. Private chats only.
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats.
 - /stickerid: reply to a sticker and get sticker id of that.
 - /getsticker: reply to a sticker and get that sticker as .png and image. 
"""

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=filters.Chat(OWNER_ID))

TIME_HANDLER = CommandHandler("time", get_time)

RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap)
INFO_HANDLER = DisableAbleCommandHandler("info", info)

ECHO_HANDLER = CommandHandler("echo", echo, filters=filters.User(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=filters.ChatType.PRIVATE)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=filters.ChatType.PRIVATE)

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)


application.add_handler(ID_HANDLER)
application.add_handler(IP_HANDLER)
application.add_handler(TIME_HANDLER)
application.add_handler(RUNS_HANDLER)
application.add_handler(SLAP_HANDLER)
application.add_handler(INFO_HANDLER)
application.add_handler(ECHO_HANDLER)
application.add_handler(MD_HELP_HANDLER)
application.add_handler(STATS_HANDLER)
application.add_handler(GDPR_HANDLER)
application.add_handler(STICKERID_HANDLER)
application.add_handler(GETSTICKER_HANDLER)
