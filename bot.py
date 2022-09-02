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
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from dotenv import load_dotenv
import os

import gspread as gs
import pandas as pd

# Load environment variables (secrets)
load_dotenv()

# Get the spreadsheet
GS_INSTANCE = gs.service_account(filename="./credentials.json")
spreadsheet = GS_INSTANCE.open_by_key(os.environ.get('SPREADSHEET_ID'))

db: dict[str, pd.DataFrame] = dict()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def load_db() -> None:
    """Load the all worksheets of the GSheet to the db dict"""
    global db
    db = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
    return


def append_row(table_name: str, row_data: list) -> None:
    """Appends a row on the DataFrame and the GSheet"""

    # Update local db
    db[table_name].loc[len(db[table_name])] = row_data

    # Update GSheet file
    spreadsheet.worksheet(table_name).append_row(row_data)

    return


def update_cell(table_name: str, row: int, col: int, new_value) -> None:
    """Updates a cell value on the DataFrame and the GSheet

    row is the number of the data row (first data row will be 1)
    col is the number of the column (first data column will be 1)
    """

    # Update local db
    db[table_name].iat[row - 1, col - 1] = new_value

    # Update GSheet file
    spreadsheet.worksheet(table_name).update_cell(row + 1, col, new_value)

    return


def get_row(table_name: str, row: int) -> dict:
    """Retrieve a row of data, assuming the local database is up to date

    row is the number of the data row (first data row will be 1)
    Returns the row as dict with the header as keys
    """
    return dict(db[table_name].iloc[row - 1])


def get_cell(table_name: str, row: int, col: int) -> any:
    """Retrieve a cell value, assuming the local database is up to date"""
    return db[table_name].iat[row - 1, col - 1]


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
    main()
