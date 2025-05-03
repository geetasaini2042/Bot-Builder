from flask import Flask, request, jsonify
from telegram_client import TelegramClient, InlineKeyboardMarkup, InlineKeyboardButton , BotServer
import requests
import threading
import json

app = Flask(__name__)
client = TelegramClient()

@app.route('/')
def home():
    return 'Telegram Webhook is running.'
@app.route('/refresh_cache')
def refresh_cache():
    load_user_status_cache()
    return "User status cache refreshed!"
######
user_status_cache = {}

def load_user_status_cache():
    global user_status_cache
    try:
        # URL se JSON data fetch karo
        response = requests.get("https://sainipankaj12.serv00.net/BotBuilder/user_status.json")
        if response.status_code == 200:
            user_status_cache = response.json()
            print("User status cache loaded successfully.")
        else:
            print(f"Failed to load user status: {response.status_code}")
    except Exception as e:
        print(f"Error loading user status: {e}")
def get_user_status(bot_token, user_id):
    return user_status_cache.get(bot_token, {}).get(str(user_id), {})
load_user_status_cache()
##########
@app.route('/<bot_token>', methods=['POST'])
def webhook(bot_token):
    update = request.get_json()
    load_user_status_cache()
    if not update:
        return jsonify({"status": "no update"}), 400

    else:
        if 'message' in update:
            handle_message(bot_token,update, update['message'])

        elif 'callback_query' in update:
            handle_callback_query(bot_token,update)


    return jsonify({"status": "ok"}), 200


def handle_message(bot_token,update, message):
    chat_id = message['chat']['id']

    if 'text' in message:
        handle_text(bot_token,update, message)

    elif 'photo' in message:
        handle_photo(bot_token,update, message)

    elif 'document' in message:
        handle_document(bot_token,update, message)
    elif 'video' in message:
        handle_video(bot_token,update, message)


def handle_text(bot_token,update, message):
    chat_id = message['chat']['id']
    user_id = message['chat']['id']
    text = message['text']
    if text == "/start":
        handle_start(bot_token, update)
    else:
        yioip = get_user_status(bot_token, user_id)
        if "status" in yioip:
            status = yioip.get("status")
            if status == "":
              print("Nothing in status")
            else:
              if status == "getting_file_description":
                BotServer.add_file_description(bot_token, full_update)
              elif status == "getting_folder_name":
                BotServer.add_folder(bot_token, full_update)
              elif status == "getting_new_folder_des":
                BotServer.add_folder(bot_token, full_update)
              elif status == "renaming_file":
                BotServer.rename_file(bot_token, full_update)  
                

def handle_photo(bot_token,full_update, message):
    chat_id = message['chat']['id']
    photos = message['photo']
    photo = photos[-1]  # Best quality
    file_id = photo['file_id']
    client.send_message(bot_token, chat_id, f"Received photo with file_id: {file_id}")

def handle_video(bot_token,full_update, message):
    chat_id = message['chat']['id']
    videos = message['video']
    video = videos[-1]  # Best quality
    file_id = video['file_id']
    client.send_message(bot_token, chat_id, f"Received photo with file_id: {file_id}")

def handle_document(bot_token,full_update, messgae):
    doc = message['document']
    chat_id = message['chat']['id']
    file_id = doc['file_id']
    file_name = doc.get('file_name', 'Unknown')
    yioip = get_user_status(bot_token, user_id)
    if "status" in yioip:
            status = yioip.get("status")
            if status == "":
              print("Nothing in status")
            else:
              if status == "awaiting_file_upload":
                BotServer.add_file(bot_token, full_update)
    client.send_message(bot_token, chat_id, f"Received document: {file_name}\nfile_id: {file_id}")


def handle_callback_query(bot_token,full_update):
    query = full_update['callback_query']
    chat_id = query['message']['chat']['id']
    message_id = query['message']['message_id']
    data = query['data']

    if data == "send_photo":
        client.send_photo(
            bot_token,
            chat_id,
            "https://placekitten.com/500/300",
            caption="Here's a photo!"
        )
    elif data == "send_doc":
        client.send_message(bot_token, chat_id, "Sending document feature coming soon!")
    elif data.startswith("add_file_des"):
      BotServer.add_file_description(bot_token, full_update)
    elif data.startswith("add_file"):
      BotServer.add_file(bot_token, full_update)
    elif data.startswith("add_folder"):
      BotServer.add_folder(bot_token, full_update)
    elif data.startswith("send_file"):
      BotServer.send_file(bot_token, full_update)
    elif data.startswith("cancle:"):
      BotServer.cancle_upload(bot_token, full_update)
    elif data.startswith(("public", "cha_file_visib", "private", "protected")):
      BotServer.change_visibility(bot_token, full_update)
    elif data.startswith("open:"):
      BotServer.open_folder(bot_token, full_update)
    elif data.startswith("rename_file"):
      BotServer.rename_file(bot_token, full_update)  
    elif data.startswith("upl_confirm"):
      BotServer.upload_confirm(bot_token, full_update)
    elif data.startswith("upl_cancle"):
      BotServer.upload_cancle(bot_token, full_update)    
      
      
      
      client.edit_message_text(bot_token, chat_id, message_id, f"Action: {data}")


def handle_start(bot_token, full_update):
        try:
            BotServer.start_command(bot_token, full_update)
        except Exception as e:
            print("Failed to post to start_command.php:", e)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
