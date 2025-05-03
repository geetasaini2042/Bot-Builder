# telegram_client.py
import requests
import json

class InlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None):
        self.text = text
        self.callback_data = callback_data
        self.url = url

    def to_dict(self):
        btn = {"text": self.text}
        if self.callback_data:
            btn["callback_data"] = self.callback_data
        if self.url:
            btn["url"] = self.url
        return btn

class InlineKeyboardMarkup:
    def __init__(self, keyboard):
        self.inline_keyboard = keyboard

    def to_dict(self):
        return {
            "inline_keyboard": [
                [button.to_dict() for button in row]
                for row in self.inline_keyboard
            ]
        }

class TelegramClient:
    def send_message(self, token, user_id, text, reply_markup=None, parse_mode=None):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": user_id,
            "text": text
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup.to_dict())
        if parse_mode:
            payload["parse_mode"] = parse_mode

        response = requests.post(url, json=payload)
        return response.json()

    def send_photo(self, token, user_id, photo_url, caption="", reply_markup=None, parse_mode=None):
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {
            "chat_id": user_id,
            "photo": photo_url,
            "caption": caption
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup.to_dict())
        if parse_mode:
            payload["parse_mode"] = parse_mode

        response = requests.post(url, json=payload)
        return response.json()

    def send_document(self, token, user_id, document_url, caption="", reply_markup=None, parse_mode=None, protect_content=False):
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        payload = {
        "chat_id": user_id,
        "document": document_url,
        "caption": caption,
        "protect_content": protect_content
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup.to_dict())
        if parse_mode:
            payload["parse_mode"] = parse_mode

        response = requests.post(url, json=payload)
        return response.json()

    def edit_message_text(self, token, chat_id, message_id, text, reply_markup=None, parse_mode=None):
        url = f"https://api.telegram.org/bot{token}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup.to_dict())
        if parse_mode:
            payload["parse_mode"] = parse_mode

        response = requests.post(url, json=payload)
        return response.json()

    def delete_message(self, token, chat_id, message_id):
       url = f"https://api.telegram.org/bot{token}/deleteMessage"
       payload = {
           "chat_id": chat_id,
           "message_id": message_id
       }

       response = requests.post(url, json=payload)
       return response.json()    
class BotServer:
    def start_command(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/start_command.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def add_file(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/add_file.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def add_folder(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/add_folder.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def send_file(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/c_send_file.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def add_file_description(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/add_file_des.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def cancle_upload(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/cancle_c_handler.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def change_visibility(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/change_visibility.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def open_folder(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/open_folder.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def rename_file(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/rename_file.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def upload_cancle(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/upl_cancle.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
    def upload_confirm(bot_token, full_update):
      requests.post(
                f"https://sainipankaj12.serv00.net/BotBuilder/upl_confirm.php?token={bot_token}",
                json=full_update,
                timeout=5
            )
