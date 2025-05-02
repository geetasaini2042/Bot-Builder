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
