from flask import Flask, request, jsonify
from keyboard_utils import get_root_inline_keyboard
import requests
from framework import on_callback_query, filters, edit_message_text, answer_callback_query, on_message, send_message, handle_webhook_request
from folder_utils import process_open_callback

# ============================
# /start HANDLER
# ============================

@on_message(filters.command("start") & filters.private())
def start_handler(bot_token, update, message):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]

    keyboard_dict, description = get_root_inline_keyboard(bot_token, user_id)

    # Send description text

    # Send inline keyboard
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": description,
        "reply_markup": keyboard_dict
    }
    requests.post(url, json=payload, timeout=2)

@on_callback_query(filters.callback_data("^open:"))
def handle_open_callback(bot_token, update, cq):
    try:
        data = cq.get("data", "")
        callback_id = cq.get("id")
        chat = cq.get("message", {}).get("chat", {})
        chat_id = chat.get("id")
        message_id = cq.get("message", {}).get("message_id")
        user = cq.get("from", {})

        # अब हम folder_utils से फ़ंक्शन कॉल करेंगे
        text, keyboard = process_open_callback(bot_token, data, user, chat_id)

        if text is not None:
            edit_message_text(bot_token, chat_id, message_id, text, reply_markup=keyboard)

        # callback को acknowledge करना ज़रूरी है
        answer_callback_query(bot_token, callback_id)
        
    except Exception as e:
        print("Error in open: callback processing:", e)
        answer_callback_query(bot_token, cq.get("id"), text="Error", show_alert=True)