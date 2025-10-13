from framework import (
    filters, on_message, on_callback_query,
    send_message, handle_webhook_request
)
from common_data import IS_TERMUX, API_URL, BOT_TOKEN, BASE_PATH, BOTS_JSON_PATH
import os, time, threading, requests, json
from flask import Flask, request, jsonify
from pathlib import Path




app = Flask(__name__)

@app.route('/webhook/<bot_token>', methods=['POST'])
def webhook1(bot_token):
    update = request.get_json()
    return handle_webhook_request(bot_token, update)


def get_bot_info(bot_token):
    """Telegram API call to get bot info"""
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if not data.get("ok"):
            return None, data.get("description", "Invalid token")
        result = data["result"]
        return {
            "id": result["id"],
            "first_name": result.get("first_name"),
            "username": result.get("username")
        }, None
    except Exception as e:
        return None, str(e)

@app.route("/add_bot", methods=["POST"])
def add_bot():
    try:
        data = request.json
        bot_token = data.get("bot_token")
        owner_id = data.get("owner_id")
        admins_ids = data.get("admins_ids", [])
        is_premium = data.get("is_premium", False)

        if not bot_token or not owner_id:
            return jsonify({"error": "bot_token और owner_id जरूरी हैं"}), 400

        # Telegram API से bot info ले
        bot_info, error = get_bot_info(bot_token)
        if error:
            return jsonify({"error": f"Invalid bot token: {error}"}), 400

        bot_username = bot_info["username"]
        bot_id = str(bot_info["id"])

        # bots.json load
        if os.path.exists(BOTS_JSON_PATH):
            with open(BOTS_JSON_PATH, "r") as f:
                bots_data = json.load(f)
        else:
            bots_data = {}

        # username check, अगर पहले से exist तो सिर्फ bot_token update
        found = False
        for b_id, b in bots_data.items():
            if b.get("username") == bot_username:
                b["bot_token"] = bot_token
                b["owner_id"] = owner_id
                b["admins_ids"] = admins_ids
                b["is_premium"] = is_premium
                found = True
                break

        if not found:
            bots_data[bot_id] = {
                "bot_token": bot_token,
                "owner_id": owner_id,
                "admins_ids": admins_ids,
                "is_premium": is_premium,
                "username": bot_username
            }

        with open(BOTS_JSON_PATH, "w") as f:
            json.dump(bots_data, f, indent=4)

        # BOT_DATA/{BOT_ID}/bot_data.json
        bot_data_dir = os.path.join(BASE_PATH, "BOT_DATA", bot_id)
        os.makedirs(bot_data_dir, exist_ok=True)

        default_json = {
            "data": {
                "id": "root",
                "name": bot_info["first_name"],
                "description": f"Welcome to {bot_info['first_name']}!",
                "type": "folder",
                "created_by": owner_id,
                "parent_id": None,
                "user_allow": [],
                "items": []
            }
        }

        bot_data_path = os.path.join(bot_data_dir, "bot_data.json")
        with open(bot_data_path, "w") as f:
            json.dump(default_json, f, indent=4)

        # ADMINS.json
        admins_json = {
            "owner": [owner_id],
            "admin": admins_ids
        }

        admins_path = os.path.join(bot_data_dir, "ADMINS.json")
        with open(admins_path, "w") as f:
            json.dump(admins_json, f, indent=4)

        return jsonify({"status": "success", "bot_id": bot_id, "username": bot_username}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Shared webhook handler
# ---------------------------

# ---------------------------
# Polling Loop for Termux
# ---------------------------
def polling_loop():
    """अगर IS_TERMUX=True है तो getUpdates से messages लाए"""
    print("🔁 Termux polling mode started...")
    offset = None

    while True:
        try:
            res = requests.get(
                f"{API_URL}/getUpdates",
                params={"timeout": 20, "offset": offset},
                timeout=25,
            )
            res.raise_for_status()  # HTTP errors raise करें
            data = res.json()

            if data.get("ok") and "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    # ⬇️ वही handler कॉल हो रहा है जो webhook में होता है
                    handle_webhook_request(BOT_TOKEN, update)

        except requests.exceptions.Timeout:
            # Timeout, बस continue
            continue
        except requests.exceptions.RequestException as e:
            print("Polling request error:", e)
            time.sleep(5)
        except Exception as e:
            print("Polling handler error:", e)
            time.sleep(5)

# ---------------------------
# Entry Point
# ---------------------------
def get_bot_folder(bot_token: str) -> str:
    #numeric = ''.join(filter(str.isdigit, bot_token))
    numeric = bot_token.split(":")[0]
    print(numeric)
    
    # Build folder path
    base_path = Path(BASE_PATH) / "BOT_DATA"
    folder_path = base_path / numeric
    
    # Create folder if not exists
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Return as string
    return str(folder_path)

