from flask import Flask, request
from framework import (
    filters, on_message, on_callback_query,
    send_message, handle_webhook_request
)
from script import app, polling_loop
import handlers, callback_data
import callback_data
from common_data import IS_TERMUX
from github import download_bots_from_github
from load_bot_data import download_all_bot_data

"""
@on_message(filters.regex("hello|hi") & filters.private())
def hello_handler(bot_token, update, message):
    chat_id = message["chat"]["id"]
    send_message(bot_token, chat_id, "🙋‍♂️ हेलो! कैसे हैं आप?")


@on_message(filters.text() & filters.group())
def group_handler(bot_token, update, message):
    chat_id = message["chat"]["id"]
    send_message(bot_token, chat_id, "👥 Group में message मिला!")
"""

if __name__ == "__main__":
    if IS_TERMUX:
        polling_loop()  # Termux mode में webhook की जगह polling
    else:
        download_bots_from_github() #REGISTERED BOT DATA
        download_all_bot_data() #BOTS INTERNAL DATA
        app.run(host="0.0.0.0", port=8000)