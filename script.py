from framework import (
    filters, on_message, on_callback_query,
    send_message, handle_webhook_request
)
from common_data import IS_TERMUX, API_URL, BOT_TOKEN, BASE_PATH, BOTS_JSON_PATH, BASE_URL,AUTH_KEY
import os, time, threading, requests, json, uuid
from flask import Flask, request, jsonify
from pathlib import Path
from flask_cors import CORS  # 🔹 Import CORS
from dotenv import load_dotenv
from github import add_new_bot, download_bots_from_github  # ⚠️ इसे सही path से import करें
from save_file_to_alt_github import save_json_to_alt_github
from save_all_registered_bots import save_registered_bot_to_github
from premium import save_a_premium, has_active_premium


app = Flask(__name__)
CORS(app) 
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
        is_premium = data.get("is_premium", False)
        is_monetized = data.get("is_monetized", False)

        if not bot_token or not owner_id:
            return jsonify({"error": "bot_token और owner_id जरूरी हैं"}), 400

        # 🔹 Telegram API से bot info ले
        bot_info, error = get_bot_info(bot_token)
        if error:
            return jsonify({"error": f"Invalid bot token: {error}"}), 400

        bot_username = bot_info["username"]
        new_bot_id = str(bot_info["id"])

        # 🔹 bots.json लोड करें
        if os.path.exists(BOTS_JSON_PATH):
            with open(BOTS_JSON_PATH, "r", encoding="utf-8") as f:
                bots_data = json.load(f)
        else:
            bots_data = {}

        # 🔹 username check
        existing_bot_id = None
        for b_id, b in bots_data.items():
            if b.get("username") == bot_username:
                existing_bot_id = b_id
                break

        webhook_url = f"{BASE_URL}/webhook/{bot_token}"

        if existing_bot_id:
            # ✅ सिर्फ token और bot_id update करें
            old_bot_data_dir = os.path.join(BASE_PATH, "BOT_DATA", existing_bot_id)
            new_bot_data_dir = os.path.join(BASE_PATH, "BOT_DATA", new_bot_id)

            if existing_bot_id != new_bot_id and os.path.exists(old_bot_data_dir):
                os.rename(old_bot_data_dir, new_bot_data_dir)
            else:
                new_bot_data_dir = old_bot_data_dir

            bots_data[new_bot_id] = bots_data.pop(existing_bot_id)
            bots_data[new_bot_id].update({
                "bot_token": bot_token,
                "webhook_url": webhook_url,
                "owner_id": owner_id
            })

        else:
            # 🔹 नया bot add करें
            bots_data[new_bot_id] = {
                "bot_token": bot_token,
                "owner_id": owner_id,
                "is_premium": is_premium,
                "username": bot_username,
                "is_monetized": is_monetized,
                "webhook_url": webhook_url
            }

            new_bot_data_dir = os.path.join(BASE_PATH, "BOT_DATA", new_bot_id)
            os.makedirs(new_bot_data_dir, exist_ok=True)

            # 🔹 BOT_DATA/{BOT_ID}/bot_data.json बनाए
            bot_data_path = os.path.join(new_bot_data_dir, "bot_data.json")
            if not os.path.exists(bot_data_path):
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
                with open(bot_data_path, "w", encoding="utf-8") as f:
                    json.dump(default_json, f, indent=4, ensure_ascii=False)

            # 🔹 ADMINS.json बनाए
            admins_json_path = os.path.join(new_bot_data_dir, "ADMINS.json")
            if not os.path.exists(admins_json_path):
                admins_data = {"owner": [int(owner_id)], "admin": []}
                with open(admins_json_path, "w", encoding="utf-8") as f:
                    json.dump(admins_data, f, indent=4, ensure_ascii=False)
            save_a_premium(price=40, days=3, bot_id=new_bot_id, plan_id="free-123-3er45tgk3-93kd939dk")     

        # ⚙️ अब common path define करें (हर हालत में)
        bot_data_path = os.path.join(new_bot_data_dir, "bot_data.json")
        admins_json_path = os.path.join(new_bot_data_dir, "ADMINS.json")
        premium_file = os.path.join(new_bot_data_dir, "premium.json")

        git_bot_data_path = os.path.join("BOT_DATA", new_bot_id, "bot_data.json")
        git_admins_json_path = os.path.join("BOT_DATA", new_bot_id, "ADMINS.json")
        git_premium_file = os.path.join("BOT_DATA", new_bot_id, "premium.json")

        # 🔹 bots.json सेव करें
        with open(BOTS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(bots_data, f, indent=4, ensure_ascii=False)

        # ✅ Telegram पर webhook सेट करें
        telegram_api = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        resp = requests.post(telegram_api, json={"url": webhook_url})
        if resp.status_code != 200:
            return jsonify({"error": "Webhook setup failed", "details": resp.text}), 500

        # ✅ GitHub अपलोड
        bot_details = bots_data[new_bot_id]
        add_new_bot(new_bot_id, bot_details)
        print(f"added: {new_bot_id}", bot_details )
        save_registered_bot_to_github(owner_id, bot_username, new_bot_id)
        save_json_to_alt_github(local_json_path=bot_data_path, github_path=git_bot_data_path)
        save_json_to_alt_github(local_json_path=admins_json_path, github_path=git_admins_json_path)

        # Premium file बनाकर सेव करें
        save_json_to_alt_github(local_json_path=premium_file, github_path=git_premium_file)

        return jsonify({
            "status": "success",
            "bot_id": new_bot_id,
            "username": bot_username,
            "webhook_url": webhook_url
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_is_monetized(bot_id: str) -> bool:
    file_path = BOTS_JSON_PATH

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            bot_info = data.get(str(bot_id))
            if not bot_info:
                print(f"Bot ID {bot_id} not found in {file_path}")
                return None

            return bot_info.get("is_monetized")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
        
def verify_bot_token(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if not data.get("ok"):
            return None, data.get("description", "Invalid token")
        return data["result"], None
    except Exception as e:
        return None, str(e)

@app.route("/auth<bot_token>/<path:file_path>", methods=["GET", "POST"])
def auth_file(bot_token, file_path):
    try:
        # ✅ पहले token verify करें
        bot_info, error = verify_bot_token(bot_token)
        if error:
            return jsonify({"error": f"Invalid bot token: {error}"}), 401

        bot_id = str(bot_info["id"])

        # ✅ Safe path बनाएं
        target_path = os.path.join(BASE_PATH, "BOT_DATA", bot_id, file_path)
        git_target_path = os.path.join("BOT_DATA", bot_id, file_path)

        # GET method → फ़ाइल मौजूद नहीं → 404
        if request.method == "GET":
            if not os.path.exists(target_path):
                return jsonify({"error": f"File not found: {file_path}"}), 404

            with open(target_path, "r") as f:
                data = json.load(f)
            return jsonify({"status": "success", "data": data}), 200

        # POST method → फ़ाइल मौजूद नहीं → नई फ़ाइल बनाएं
        elif request.method == "POST":
            new_data = request.json
            if not isinstance(new_data, dict):
                return jsonify({"error": "Invalid JSON body"}), 400

            # अगर फ़ाइल या folder नहीं है, तो बनाएं
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w") as f:
                json.dump(new_data, f, indent=4)

            save_json_to_alt_github(local_json_path=target_path, github_path=git_target_path)
            return jsonify({"status": "updated", "file": file_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/check_premium/<auth_key>", methods=["GET"])
def check_premium(auth_key):
    # 🔒 Auth-Key Verify
    if auth_key != AUTH_KEY:
        return jsonify({"status": False, "message": "❌ Invalid Auth-Key!"}), 401

    # 🔍 Required Parameter
    bot_id = request.args.get("bot_id")
    if not bot_id:
        return jsonify({"status": False, "message": "⚠️ Missing bot_id!"}), 400

    # ✅ Check Premium
    try:
        active = has_active_premium(bot_id)
        return jsonify({
            "status": True,
            "bot_id": bot_id,
            "premium_active": active,
            "message": "✅ Premium is active!" if active else "❌ No active premium found."
        })
    except Exception as e:
        return jsonify({"status": False, "message": f"❌ Error: {str(e)}"}), 500
@app.route("/add_premium/<auth_key>", methods=["GET"])
def add_premium(auth_key):
    # 🔒 Auth-Key Check
    if auth_key != AUTH_KEY:
        return jsonify({"status": False, "message": "❌ Invalid Auth-Key!"}), 401

    # 🔍 Required params
    bot_id = request.args.get("bot_id")
    price = request.args.get("price", "free")
    days = request.args.get("days", "3")
    plan_id = request.args.get("plan_id")  # optional but used to prevent duplicate

    if not bot_id:
        return jsonify({"status": False, "message": "⚠️ Missing bot_id!"}), 400

    try:
        days = int(days)
    except:
        return jsonify({"status": False, "message": "⚠️ Invalid days value!"}), 400

    # अगर plan_id नहीं भेजा गया तो नया बना दो
    if not plan_id:
        plan_id = str(uuid.uuid4())

    try:
        # ✅ Save Premium (handles duplicates internally)
        entry = save_a_premium(price, days, BASE_PATH, bot_id, plan_id)

        # अगर duplicate था तो message अलग होगा
        message = "✅ Premium added successfully!"
        if entry.get("plan_id") == plan_id and "duplicate" in entry.get("status", ""):
            message = "⚠️ Duplicate request — plan already exists!"

        return jsonify({
            "status": True,
            "message": message,
            "bot_id": bot_id,
            "plan_id": entry["plan_id"],
            "price": entry["price"],
            "days": entry["days"],
            "start_date_and_time": entry["start_date_and_time"],
            "expire_date_and_time": entry["expire_date_and_time"]
        })

    except Exception as e:
        return jsonify({"status": False, "message": f"❌ Error: {str(e)}"}), 500
@app.route("/edit<bot_token>/<path:file_path>", methods=["GET", "POST"])
def edit_file_ui(bot_token, file_path):
    try:
        # ✅ Token verify करें
        bot_info, error = verify_bot_token(bot_token)
        if error:
            return f"<h3 style='color:red;'>Invalid bot token: {error}</h3>", 401

        bot_id = str(bot_info["id"])
        target_path = os.path.join(BASE_PATH, "BOT_DATA", bot_id, file_path)
        string = str(target_path)
        git_target_path = os.path.join("BOT_DATA", bot_id, file_path)

        if not os.path.exists(target_path):
            return f"<h3 style='color:red;'>File not found: {file_path}</h3>", 404
        if "premium.json" in string:
          return f"<h3 style='color:red;'>file not allowed to be edit</h3>", 203

        # ✅ GET method → JSON content UI में दिखाओ
        if request.method == "GET":
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            html = f"""
            <html>
            <head>
                <title>Edit {file_path}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f5f5f5;
                        padding: 20px;
                    }}
                    h2 {{
                        color: #333;
                    }}
                    textarea {{
                        width: 100%;
                        height: 400px;
                        font-family: monospace;
                        font-size: 14px;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 6px;
                        background: #fff;
                    }}
                    button {{
                        margin-top: 15px;
                        padding: 10px 20px;
                        background: #007bff;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }}
                    button:hover {{
                        background: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <h2>Editing File: {file_path}</h2>
                <form method="POST">
                    <textarea name="content">{content}</textarea><br>
                    <button type="submit">💾 Save Changes</button>
                </form>
            </body>
            </html>
            """
            return html

        # ✅ POST method → File में save करें
        elif request.method == "POST":
            new_content = request.form.get("content", "")
            try:
                json_object = json.loads(new_content)  # Validate JSON
            except json.JSONDecodeError as e:
                return f"<h3 style='color:red;'>Invalid JSON format: {e}</h3>", 400

            # Save file locally
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(json_object, f, indent=4, ensure_ascii=False)

            # GitHub पर भी save करें
            result = save_json_to_alt_github(local_json_path=target_path, github_path=git_target_path)

            return f"<h3 style='color:green;'>✅ File updated successfully!</h3><a href=''>🔄 Go back</a>"

    except Exception as e:
        return f"<h3 style='color:red;'>Error: {str(e)}</h3>", 500
@app.route("/owner/<int:owner_id>", methods=["GET"])
def get_owner_bots(owner_id):
    try:
        # bots.json load करें
        if not os.path.exists(BOTS_JSON_PATH):
            return jsonify({"error": "bots.json not found"}), 404

        with open(BOTS_JSON_PATH, "r") as f:
            bots_data = json.load(f)

        # Filter करें owner_id से
        owner_bots = []
        for bot_id, details in bots_data.items():
            if str(details.get("owner_id")) == str(owner_id):
                bot_info = {
                    "bot_id": bot_id,
                    "bot_token": details.get("bot_token"),
                    "username": details.get("username"),
                    "owner_id": details.get("owner_id"),
                    "admins_ids": details.get("admins_ids", []),
                    "is_premium": details.get("is_premium", False)
                }
                owner_bots.append(bot_info)

        return jsonify({
            "owner_id": owner_id,
            "bot_count": len(owner_bots),
            "bots": owner_bots
        }), 200

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
            #print(data)

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

