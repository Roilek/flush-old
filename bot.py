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
from gspread import Client
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from dotenv import load_dotenv
import os

import gspread
import csv

# Load environment variables (secrets)
load_dotenv()

# Get the spreadsheet
GSPREAD_INSTANCE = gspread.service_account(filename="./credentials.json")
spreadsheet = GSPREAD_INSTANCE.open_by_key(os.environ.get('SPREADSHEET_ID'))

# database folder name
DATABASE_FOLDER_NAME = "database"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def load_db() -> None:
    """Load the all worksheets to csv files"""

    for worksheet in spreadsheet.worksheets():
        filename = DATABASE_FOLDER_NAME + "/" + worksheet.title + ".csv"
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(worksheet.get_all_values())

    return


def writerow(table_name: str, row_data: list) -> None:
    """Appends a row on the csv and the GSheet"""

    # Update csv file
    filename = DATABASE_FOLDER_NAME + "/" + table_name + ".csv"
    with open(filename, "a") as f:
        writer = csv.writer(f)
        writer.writerow(row_data)

    # Update GSheet file
    spreadsheet.worksheet(table_name).append_row(row_data)

    return


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""

    # Cache all the data
    load_db()

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(os.environ.get('TOKEN'), use_context=True)


    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    #main()
    load_db()
    #writerow("enigma", [2, "name", "description", "answer", "Author", "feedback"])