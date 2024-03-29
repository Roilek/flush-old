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
import json
import logging
import telegram
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from dotenv import load_dotenv
import os

import gspread as gs
import pandas as pd

# Load environment variables (secrets)
load_dotenv()

# For debug mode
DEBUG = int(os.environ.get('DEBUG'))

# Get the spreadsheet
GS_INSTANCE = gs.service_account(filename="./credentials.json")
spreadsheet = GS_INSTANCE.open_by_key(os.environ.get('SPREADSHEET_ID'))

db: dict[str, pd.DataFrame] = dict()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

EXPECT_ENIGMA_ID, EXPECT_ANSWER_TO_ENIGMA, CONTACT, SUGGEST, REPORT, ADD_ENIGMA = range(6)

CONFIG_TABLE = "config"
CONFIG_ROW_OFFSET, CONFIG_USERS_UUID_OFFSET = range(2)

ENIGMA_TABLE = "enigma"
ENIGMA_UUID, ENIGMA_NAME, ENIGMA_DESCRIPTION, ENIGMA_ANSWER, ENIGMA_AUTHOR, ENIGMA_FEEDBACK = range(6)

USERS_TABLE = "users"
USERS_UUID, USERS_ID, USERS_FIRST_NAME, USERS_LAST_NAME, USERS_USERNAME, USERS_SCORE, USERS_CURRENT_ENIGMA = range(7)

USERS_ENIGMA_TABLE = "users_enigma"
USERS_ENIGMA_UUID, USERS_ENIGMA_TIMESTAMP, USERS_ENIGMA_USER_ID, USERS_ENIGMA_ENIGMA_ID, USERS_ENIGMA_ATTEMPT_DATA, USERS_ENIGMA_VALIDATED = range(
    6)


def load_db() -> None:
    """Load the all worksheets of the GSheet to the db dict

    :returns: None
    """
    global db
    db = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
    return


def append_row(table_name: str, row_data: list) -> int:
    """Appends a row on the DataFrame and the GSheet

    :param table_name: The name of the table to modify
    :type table_name: str
    :param row_data: The list of data to register
    :type row_data: list

    :returns: Returns the number of the added row
    :rtype: int
    """

    # Update local db
    db[table_name].loc[len(db[table_name])] = row_data

    # Update GSheet file
    spreadsheet.worksheet(table_name).append_row([str(item) for item in row_data])

    return len(db[table_name]) - 1


def update_cell(table_name: str, row: int, col: int, new_value: any) -> None:
    """Updates a cell value on the DataFrame and the GSheet

    :param table_name: The name of the table to modify
    :type table_name: str
    :param row: The index of the row (0 is the first data row, without the headers)
    :type row: int
    :param col: The index of the column
    :type col: int
    :param new_value: The new value to register
    :param new_value: any

    :returns: None
    """

    # Update local db
    db[table_name].iat[row, col] = new_value

    # Update GSheet file
    spreadsheet.worksheet(table_name).update_cell(row + 2, col + 1, str(new_value))

    return


def get_table(table_name: str) -> list:
    """Retrieve a table of data, assuming the local database is up to date

    :param table_name: The name of the table to read from
    :type table_name: str

    :returns: Returns the list of values of the required table
    :rtype: list
    """
    return db[table_name].values.tolist()


def get_row(table_name: str, row: int) -> list:
    """Retrieve a row of data, assuming the local database is up to date

    :param table_name: The name of the table to read from
    :type table_name: str
    :param row: The index of the row (0 is the first data row, without the headers)
    :type row: int

    :returns: Returns the values of the required row
    :rtype: list
    """
    return db[table_name].iloc[row].values.tolist()


def get_col(table_name: str, col: int) -> list:
    """Retrieve a column of data, assuming the local database is up to date

    :param table_name: The name of the table to read from
    :type table_name: str
    :param col: The index of the column
    :type col: int

    :returns: Returns the values of the required column
    :rtype: list
    """
    return db[table_name].iloc[:, col].values.tolist()


def get_cell(table_name: str, row: int, col: int) -> any:
    """Retrieve a cell's data, assuming the local database is up to date

    :param table_name: The name of the table to read from
    :type table_name: str
    :param row: The index of the row (0 is the first data row, without the headers)
    :type row: int
    :param col: The index of the column
    :type col: int

    :returns: Returns the values of the required cell
    :rtype: any
    """

    return db[table_name].iat[row, col]


def get_cell_last_cell_of_col(table_name: str, col: int) -> any:
    """Retrieve the data in the last cell of the specified column

    :param table_name: The name of the table to modify
    :type: table_name: str
    :param col: The index of the column
    :type: col: int

    :returns: Returns the value of the required cell
    :rtype: any
    """
    return db[table_name].iat[len(db[table_name]) - 1, col]


def register_new_user(user: dict) -> None:
    """Registers a new user to the database

    :param user: The user dict of informations as sent by Telegram
    :type user: dict

    :returns: None
    """

    # Get the next uuid to attribute
    uuid_offset = int(get_cell(CONFIG_TABLE, 0, CONFIG_USERS_UUID_OFFSET))

    # Register the new user with a new uuid
    append_row(USERS_TABLE, [int(uuid_offset), int(user.id), user.first_name, user.last_name, user.username, 0, 0])

    # Update the uuid
    update_cell(CONFIG_TABLE, 0, CONFIG_USERS_UUID_OFFSET, uuid_offset + 1)

    return


def start(update: Update, context: CallbackContext) -> None:
    """Greets the old user and greet + register the new user"""

    if DEBUG:
        print(update)

    user = update.message.from_user
    user_ids = get_col(USERS_TABLE, USERS_ID)

    if user.id in user_ids:
        message = "Welcome back " + get_cell(USERS_TABLE, user_ids.index(user.id), USERS_FIRST_NAME)
    else:
        register_new_user(user)
        message = "Welcome " + user.first_name
    message += "\nPlease use /new_enigma to start guessing!"
    message += "\nYou can also use /help to see everything this bot can do!"
    update.message.reply_text(message)

    return


def new_enigma(update: Update, context: CallbackContext) -> int:
    """Entry point of the conversation, asks the number of the enigma to the user"""
    update.message.reply_text("Please send me the id of the enigma you want to try to solve (or /cancel)")
    return EXPECT_ENIGMA_ID


def construct_enigma_message(enigma_id: int) -> str:
    """Constructs and formats enigma message from enigma id

    :param enigma_id: The id of the enigma
    :type enigma_id: int

    :returns: The html string to be sent to the user
    :rtype: str
    """
    enigma_ids = get_col(ENIGMA_TABLE, ENIGMA_UUID)

    message_parts = list()
    message_parts.append(''.join(["<i>Enigma ", str(enigma_id), "</i>"]))
    message_parts.append(''.join(["<b>", get_cell(ENIGMA_TABLE, enigma_ids.index(enigma_id), ENIGMA_NAME), "</b>"]))
    message_parts.append(get_cell(ENIGMA_TABLE, enigma_ids.index(enigma_id), ENIGMA_DESCRIPTION))

    return '\n'.join(message_parts)


def confirm_and_send_enigma(update: Update, context: CallbackContext) -> int:
    """Checks if the enigma id entered by the user is valid and sends the enigma"""
    if not update.message.text.isdigit():
        update.message.reply_text("The enigma id has to be an integer! Please send me a valid id")
        return new_enigma(update, context)

    enigma_id = int(update.message.text)
    enigma_ids = get_col(ENIGMA_TABLE, ENIGMA_UUID)

    if enigma_id not in enigma_ids:
        update.message.reply_text("This id is not valid! Please send me a valid id")
        return new_enigma(update, context)

    if DEBUG:
        print(enigma_ids)

    previous_attempts = [row for row in get_table(USERS_ENIGMA_TABLE) if (
                row[USERS_ENIGMA_USER_ID] == update.effective_user.id and row[USERS_ENIGMA_ENIGMA_ID] == enigma_id) and
                         row[USERS_ENIGMA_VALIDATED]]

    if len(previous_attempts) > 0:
        update.message.reply_text(construct_enigma_message(enigma_id), ParseMode.HTML)
        update.message.reply_text("You have already found the answer to this enigma: <u>" + str(previous_attempts[0][
            USERS_ENIGMA_ATTEMPT_DATA]) + "</u>", ParseMode.HTML)
        return new_enigma(update, context)
    # Updates the current enigma of the user
    update_cell(USERS_TABLE, get_col(USERS_TABLE, USERS_ID).index(int(update.message.from_user.id)),
                USERS_CURRENT_ENIGMA, enigma_id)
    # Send the enigma to the user
    update.message.reply_text(construct_enigma_message(enigma_id), ParseMode.HTML)
    update.message.reply_text("Please send me the answer you think is correct! (or /cancel)")
    return EXPECT_ANSWER_TO_ENIGMA


def validate_enigma(update: Update, context: CallbackContext) -> int:
    """Validates the answer of the user"""

    user_answer = update.message.text
    enigma_id = get_cell(USERS_TABLE, get_col(USERS_TABLE, USERS_ID).index(update.message.from_user.id),
                         USERS_CURRENT_ENIGMA)
    right_answer = str(get_cell(ENIGMA_TABLE, get_col(ENIGMA_TABLE, ENIGMA_UUID).index(enigma_id), ENIGMA_ANSWER))

    if DEBUG:
        print(user_answer)
        print(right_answer)

    if user_answer in right_answer.split(', '):
        update.message.reply_text(
            "Congratulations, you've found the right answer! Send /new_enigma to start a new one!")
        # Updates the current enigma of the user to put it back to zero
        update_cell(USERS_TABLE, get_col(USERS_TABLE, USERS_ID).index(int(update.message.from_user.id)),
                    USERS_CURRENT_ENIGMA, 0)
        append_row(USERS_ENIGMA_TABLE, [get_cell_last_cell_of_col(USERS_ENIGMA_TABLE, USERS_ENIGMA_UUID), 0,
                                        int(update.message.from_user.id), enigma_id, user_answer, 1])
        return ConversationHandler.END
    else:
        update.message.reply_text("Sorry, your answer is wrong... You can try again or send /cancel to stop trying.")
        append_row(USERS_ENIGMA_TABLE, [get_cell_last_cell_of_col(USERS_ENIGMA_TABLE, USERS_ENIGMA_UUID), 0,
                                        int(update.message.from_user.id), enigma_id, user_answer, 0])
        return EXPECT_ANSWER_TO_ENIGMA


def cancel(update: Update, context: CallbackContext) -> int:
    """Handles the abortion of the enigma selection and solving attempt"""
    update.message.reply_text(
        'Enigma selection or resolution cancelled by user. Bye. Send /new_enigma to start again')
    update_cell(USERS_TABLE, get_col(USERS_TABLE, USERS_ID).index(int(update.message.from_user.id)),
                USERS_CURRENT_ENIGMA, 0)
    return ConversationHandler.END


def contact(update: Update, context: CallbackContext) -> int:
    """Entry point to contact the bot designers"""
    update.message.reply_text(
        'Send me anything you want to say to my developers, I\'ll let them know !')
    return CONTACT


def suggest(update: Update, context: CallbackContext) -> int:
    """Entry point to make a suggestion the bot designers"""
    update.message.reply_text(
        'Send me your suggestion, I will forward it to my developers!')
    return SUGGEST


def report(update: Update, context: CallbackContext) -> int:
    """Entry point to contact the bot designers"""
    update.message.reply_text(
        'Send me a message to report any bug you would spot. If you think an answer should be considered as valid but '
        'is not, please let me know!')
    return REPORT


def add_enigma(update: Update, context: CallbackContext) -> int:
    """Entry point to contact the bot designers"""
    update.message.reply_text(
        'You want to suggest a new enigma? Please send your idea and my dev team will discuss it with you!')
    return ADD_ENIGMA


def forward(update: Update, context: CallbackContext) -> int:
    """Forwards the message in the designer's group"""
    update.message.forward(os.environ.get('DESIGNER_GROUP_ID'))
    update.message.reply_text("Your message have been forwarded to the developer team! Thanks!\nYou can add comments "
                              "by replaying to the message you sent or to the answer you might received\nSend "
                              "/new_enigma to start guessing again")
    return ConversationHandler.END


def help(update, context):
    """Send a message when the command /help is issued."""
    list_commands = {
        "/start": "See the greeting message",
        "/help": "See this help message",
        "/new_enigma": "Start guessing!",
        "/stats": "[Not implemented yet]",
        "/contact": "Contact the dev team",
        "/suggest": "Suggest a new feature to the dev team",
        "/add_enigma": "Suggest a new enigma to the team",
        "/report": "Report a problem (missing indices, my answer should be right but bot says it is wrong",
    }
    message = "Here is what this bot can do"
    update.message.reply_text("Here is what this bot can do:" + "\n  - ".join(
        ['', *[command + ": " + meaning for command, meaning in list_commands.items()]]))
    return


def warn(update, context: CallbackContext):
    """Warns the user the message has not been understood."""
    if DEBUG:
        print(update)
    if update.message.reply_to_message:
        if update.message.chat.type == "private":
            update.message.forward(os.environ.get('DESIGNER_GROUP_ID'))
        else:
            context.bot.send_message(update.message.reply_to_message.forward_from.id, update.message.text)
    else:
        update.message.reply_text("Sorry I did not understand, please try to send /start or /new_enigma to start again")
    return


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    return


def update_db(update, context):
    """Updates the db by calling load_db"""
    load_db()
    update.message.reply_text("The database hase been updated!")
    return


def main():
    """Start the bot."""

    # Cache all the data
    load_db()

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(os.environ.get('TOKEN'), use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("update", update_db))

    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler('new_enigma', new_enigma), CommandHandler('contact', contact), CommandHandler('suggest', suggest), CommandHandler('report', report), CommandHandler('add_enigma', add_enigma)],
        states={
            EXPECT_ENIGMA_ID: [MessageHandler(Filters.text & (~ Filters.command), confirm_and_send_enigma)],
            EXPECT_ANSWER_TO_ENIGMA: [MessageHandler(Filters.text & (~ Filters.command), validate_enigma)],
            CONTACT: [MessageHandler(~ Filters.command, forward)],
            SUGGEST: [MessageHandler(~ Filters.command, forward)],
            REPORT: [MessageHandler(~ Filters.command, forward)],
            ADD_ENIGMA: [MessageHandler(~ Filters.command, forward)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        run_async=True,
        allow_reentry=True,
        per_user=True
    ))

    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text, warn))

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    updater.bot.sendMessage(chat_id=os.environ.get('DESIGNER_GROUP_ID'), text="👋 Hi! I'm awake!")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
