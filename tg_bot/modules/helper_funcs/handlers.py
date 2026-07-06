from telegram import Update
from telegram.ext import CommandHandler, MessageHandler

CMD_STARTERS = ('/', '!')


class CustomCommandHandler(CommandHandler):
    def check_update(self, update):
        if isinstance(update, Update) and (update.message or update.edited_message and self.allow_edited):
            message = update.message or update.edited_message
            if message.text and len(message.text) > 1:
                fst_word = message.text.split(None, 1)[0]
                if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
                    command = fst_word[1:].split('@')
                    bot = update.get_bot()
                    if bot:
                        command.append(bot.username)
                    if self.filters is None:
                        res = True
                    elif isinstance(self.filters, list):
                        res = any(f.check_update(update) for f in self.filters)
                    else:
                        res = self.filters.check_update(update)
                    return res and (command[0].lower() in self.commands
                                    and (len(command) < 2 or not bot or command[1].lower() == bot.username.lower()))
            return False
