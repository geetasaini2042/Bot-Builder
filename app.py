from flask import Flask, request, jsonify
from telegram_client import TelegramClient, InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)
client = TelegramClient()

@app.route('/')
def home():
    return 'Telegram Webhook is running.'

@app.route('/<bot_token>', methods=['POST'])
def webhook(bot_token):
    update = request.get_json()

    if not update:
        return jsonify({"status": "no update"}), 400

    try:
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']

            # TEXT MESSAGE
            if 'text' in message:
                text = message['text']
                if text == "/start":
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("Send Photo", callback_data="send_photo")],
                        [InlineKeyboardButton("Send Document", callback_data="send_doc")]
                    ])
                    client.send_message(bot_token, chat_id, "Welcome! Choose an option:", reply_markup=keyboard)
                else:
                    client.send_message(bot_token, chat_id, f"You said: {text}")

            # PHOTO MESSAGE
            elif 'photo' in message:
                photo = message['photo'][-1]  # Best quality
                file_id = photo['file_id']
                client.send_message(bot_token, chat_id, f"Received photo with file_id: {file_id}")

            # DOCUMENT MESSAGE
            elif 'document' in message:
                doc = message['document']
                file_id = doc['file_id']
                file_name = doc.get('file_name', 'Unknown')
                client.send_message(bot_token, chat_id, f"Received document: {file_name}\nfile_id: {file_id}")

        # CALLBACK QUERY HANDLING
        elif 'callback_query' in update:
            query = update['callback_query']
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

            # Optional: Edit message to show action taken
            client.edit_message_text(bot_token, chat_id, message_id, f"Action: {data}")

    except Exception as e:
        print("Error:", e)

    return jsonify({"status": "ok"}), 200

app.run(host="0.0.0.0", port=8000)    
