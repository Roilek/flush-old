#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import telegram
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from dotenv import load_dotenv
import os

import gspread

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv()
DEBUG = os.environ.get("DEBUG")


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def enigma(update: Update, context: CallbackContext) -> None:
    """Reacts to a n-digit code to select the enigma"""
    update.message.reply_text("Please send me the n-digit code you see on the door to go on to the enigma")
    return


def handle_text(update: Update, context: CallbackContext) -> None:
    """Dispatcher to handle the given text"""
    data = update.message.text

    # Is data an enigma id?
    if data.startswith('#'):
        if DEBUG:
            update.message.reply_text("Let's start enigma number " + data[1:])  # to remove when todo is done
        # TODO check if data[1:] is in the list of existing enigmas id
    # If data is not an enigma id, it must be an answer
    elif True:  # TODO Test if the user has already an enigma that he is trying to solve
        if DEBUG:
            update.message.reply_text("I see this is an answer to an enigma")
        # TODO check if the answer to the enigma currently tried by the user is in data
    else:
        update.message.reply_text("You have to select an enigma before trying to solve it :)")

    return


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    gc = gspread.service_account(filename="./credentials.json")

    load_dotenv()

    updater = Updater(os.environ.get('TOKEN'), use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("enigma", enigma))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, handle_text))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
