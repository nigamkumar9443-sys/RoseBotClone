from telegram import Update
from telegram.ext import CommandHandler

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import application

from requests import get

async def ud(update: Update, context):
  message = update.effective_message
  text = message.text[len('/ud '):]
  results = get(f'http://api.urbandictionary.com/v0/define?term={text}').json()
  reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
  await message.reply_text(reply_text)

__help__ = """
 - /ud:{word} Type the word or expression you want to search use. like /ud telegram Word: Telegram Definition: A once-popular system of telecommunications, in which the sender would contact the telegram service and speak their [message] over the [phone]. The person taking the message would then send it, via a teletype machine, to a telegram office near the receiver's [address]. The message would then be hand-delivered to the addressee. From 1851 until it discontinued the service in 2006, Western Union was the best-known telegram service in the world.
"""

__mod_name__ = "Urban dictionary"
  
ud_handle = DisableAbleCommandHandler("ud", ud)

application.add_handler(ud_handle)
