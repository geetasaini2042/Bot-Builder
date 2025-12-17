import json, uuid, threading
from typing import Union
import os, json
from typing import Union
from framework import on_callback_query,get_markdown,esc, filters, edit_message_text, answer_callback_query, on_message, send_with_error_message, send_audio, send_video, send_photo, send_api, send_document, delete_message, edit_message
from framework import (
    on_message, filters,
    send_message, edit_message_text
)
from collections import defaultdict
import time
from pathlib import Path
from common_data import BASE_PATH,BASE_URL
from script import get_bot_folder, get_is_monetized
from status_filters import StatusFilter
from framework import InlineKeyboardButton, InlineKeyboardMarkup, escape_markdown
from folder_utils import generate_folder_keyboard
from save_file_to_alt_github import save_json_to_alt_github


def get_status_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "status_user.json")

def get_temp_folder(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "temp_folder.json")

def get_more_contents_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "FILE_OTHER.json")

def get_file_log_id(bot_token: str) -> int | None:
    # 🔹 FILE_LOG.json का path प्राप्त करें
    file_path = os.path.join(get_bot_folder(bot_token), "FILE_LOG.json")

    # 🔹 अगर फ़ाइल नहीं है तो कुछ भी return न करें
    if not os.path.exists(file_path):
        return None

    try:
        # 🔹 JSON फ़ाइल पढ़ें
        with open(file_path, "r") as f:
            data = json.load(f)

        # 🔹 FILE_LOGS key से वैल्यू निकालें (अगर नहीं है तो None लौटे)
        return data.get("FILE_LOGS")

    except Exception as e:
        print(f"❌ Error reading FILE_LOG.json: {e}")
        return None
def get_pre_files_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "PREMIUM_PDF.json")
def get_temp_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "temp_file.json")
def get_temp_webapp_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "temp_web_url.json")  
    
def get_temp_url_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "temp_url.json")
    
def get_data_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "bot_data.json")

def get_created_by_from_folder(bot_token,folder_id):
    data_file = get_data_file(bot_token)
    try:
        with open(data_file) as f:
            bot_data = json.load(f)
    except:
        return None

    def find_created_by(folder):
        if folder.get("id") == folder_id and folder.get("type") == "folder":
            return folder.get("created_by")
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                result = find_created_by(item)
                if result is not None:
                    return result
        return None

    root = bot_data.get("data", {})
    return find_created_by(root)

# ------------------------------
#   File Utilities
# ------------------------------

def load_json_file(path: str) -> dict:
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json_file(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def set_user_status(bot_token: str, user_id: int, status: str):
    path = get_status_file(bot_token)
    data = load_json_file(path)
    data[str(user_id)] = status
    save_json_file(path, data)


def save_temp_folder(bot_token: str, user_id: int, folder_data: dict):
    path = get_temp_folder(bot_token)
    data = load_json_file(path)
    data[str(user_id)] = folder_data
    save_json_file(path, data)


def load_bot_data(bot_token: str) -> Union[dict, list, None]:
    path = get_data_file(bot_token)
    return load_json_file(path)

# 🔍 Folder search utility
def find_folder_by_id(current_folder: dict, target_id: str):
    if current_folder.get("id") == target_id and current_folder.get("type") == "folder":
        return current_folder

    for item in current_folder.get("items", []):
        if item.get("type") == "folder":
            result = find_folder_by_id(item, target_id)
            if result:
                return result
    return None


def is_user_action_allowed(folder_id, action, bot_token):
    data_file =  get_data_file(bot_token)
    try:
        with open(data_file) as f:
            data = json.load(f)
    except:
        return False

    def find_folder(folder):
        if folder.get("id") == folder_id and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                result = find_folder(item)
                if result:
                    return result
        return None

    root = data.get("data", {})
    folder = find_folder(root)
    if not folder:
        return False

    return action in folder.get("user_allow", [])
# 🧠 Callback: Add Folder

def ADMINS(bot_id: str) -> list:

    admin_file = Path(BASE_PATH) / "BOT_DATA" / bot_id / "ADMINS.json"

    if not admin_file.exists():
        return []

    try:
        with admin_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            owners = data.get("owner", [])
            admins = data.get("admin", [])
            return owners + admins
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {admin_file}: {e}")
        return []
@on_callback_query(filters.callback_data("^add_folder:"))
def add_folder_callback(bot_token, update, cq):
  #  try:
        bot_id = bot_token.split(":")[0]
        data = cq.get("data", "")
        callback_id = cq.get("id")
        user = cq.get("from", {})
        user_id = user.get("id")
        chat = cq.get("message", {}).get("chat", {})
        chat_id = chat.get("id")
        message_id = cq.get("message", {}).get("message_id")

        parent_id = data.split(":", 1)[1]

        # Load bot data
        full_data = load_bot_data(bot_token)
        if not full_data:
            answer_callback_query(bot_token, callback_id, text="⚠ Data file missing.", show_alert=True)
            return

        root = full_data.get("data", {})
        parent_folder = find_folder_by_id(root, parent_id)

        if not parent_folder:
            answer_callback_query(bot_token, callback_id, text="❌ Parent folder not found.", show_alert=True)
            return

        # Permissions check (placeholder functions)
        if (not is_user_action_allowed(parent_id, "add_folder", bot_token)
            and user_id not in ADMINS(str(bot_id))
            and get_created_by_from_folder(bot_token,parent_id) != user_id):
            answer_callback_query(bot_token, callback_id, text="❌ You are not allowed to add a folder.", show_alert=True)
            return

        # Save temp folder draft
        temp_data = {
            "user_id": user_id,
            "parent_id": parent_id,
            "parent_name": parent_folder["name"],
            "name": "",
            "description": "",
            "user_allow": []
        }

        save_temp_folder(bot_token, user_id, temp_data)
        set_user_status(bot_token, user_id, f"getting_folder_name:{parent_id}")

        # Edit message
        text = (
    f"{esc('📁 Adding new folder under:')} "
    f"*{esc(parent_folder['name'])}*\n\n"
    f"{esc('✍️ Please send the ')}*name*{esc(' of the new folder.')}"
)

        edit_message_text(bot_token, chat_id, message_id, text)

        answer_callback_query(bot_token, callback_id)

@on_message(filters.private() & filters.text() & StatusFilter("getting_folder_name"))
def receive_folder_name(bot_token, update, msg):
    user_id = msg.get("from", {}).get("id")
    text = msg.get("text", "").strip()

    # --- बाकी का लोड/सेव कोड (Same as before) ---
    status_file = get_status_file(bot_token)
    status_data = load_json_file(status_file)
    status = status_data.get(str(user_id), "")
    parent_id = status.split(":", 1)[1]

    temp_file = get_temp_folder(bot_token)
    temp_data = load_json_file(temp_file)
    folder_data = temp_data.get(str(user_id), {})
    folder_data["name"] = text # यहाँ हम original text ही सेव करेंगे (database के लिए)

    temp_data[str(user_id)] = folder_data
    save_json_file(temp_file, temp_data)

    status_data[str(user_id)] = f"getting_folder_description:{parent_id}"
    save_json_file(status_file, status_data)

    # --- REPLY भेजने वाला हिस्सा (यहाँ सुधार किया है) ---
    chat_id = msg.get("chat", {}).get("id")
    msg_to_send = (
        f"{esc('✅ Name Saved!')} `{esc(text)}`\n"
        f"{esc('Now Please Send a folder message..')}"
    )

    send_message(bot_token, chat_id, msg_to_send)


@on_message(filters.private() & filters.text() & StatusFilter("getting_folder_description"))
def receive_folder_description(bot_token, update, msg):
    user_id = msg["from"]["id"]
    #text = msg.get("text", "").strip()
    description = get_markdown(msg)
    
    status_file = get_status_file(bot_token)
    status_data = load_json_file(status_file)
    status = status_data.get(str(user_id), "")
    parent_id = status.split(":", 1)[1] if ":" in status else "root"

    # ---------------------------
    # Load temp folder data
    # ---------------------------
    temp_file = get_temp_folder(bot_token)
    temp_data = load_json_file(temp_file)
    folder_data = temp_data.get(str(user_id), {})
    folder_data["description"] = description
    temp_data[str(user_id)] = folder_data
    save_json_file(temp_file, temp_data)

    # ---------------------------
    # Update status to permissions
    # ---------------------------
    status_data[str(user_id)] = f"setting_folder_permissions:{parent_id}"
    save_json_file(status_file, status_data)

    # ---------------------------
    # Show toggling buttons
    # ---------------------------
    buttons = [
        [
            InlineKeyboardButton("➕ Add File ❌", callback_data="toggle:add_file"),
            InlineKeyboardButton("📁 Add Folder ❌", callback_data="toggle:add_folder")
        ],
        [
            InlineKeyboardButton("🔗 Add URL ❌", callback_data="toggle:add_url"),
            InlineKeyboardButton("🧩 Add WebApp ❌", callback_data="toggle:add_webapp")
        ],
        [
            InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm_folder")
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    chat_id = msg["chat"]["id"]
        # यह मैसेज यूजर को साफ-साफ बताएगा कि उसे क्या करना है
    msg_text = (
        f"*{esc('✅ Description Saved Successfully!')}*\n\n"
        f"{esc('Now, please configure the permissions for this folder.')}\n"
        f"{esc('Use the buttons below to select which types of content a user is allowed to add here.')}\n\n"
        f"{esc('👇 Toggle the options to Allow/Disallow:')}"
    )
    send_message(
        bot_token,
        chat_id,
        msg_text,
        reply_markup=keyboard
    )

@on_callback_query(filters.callback_data("^toggle:"))
def toggle_permission_handler(bot_token, update, cq):
    user_id = str(cq["from"]["id"])
    callback_id = cq.get("id")

    # 1. Spinner को रोको
    answer_callback_query(bot_token, callback_id)

    permission = cq.get("data", "").split(":", 1)[1]
    
    # Load Data
    temp_file = get_temp_folder(bot_token)
    temp_data = load_json_file(temp_file)
    folder = temp_data.get(user_id)

    if not folder:
        answer_callback_query(bot_token, callback_id, text="❌ Folder data not found!", show_alert=True)
        return

    # Toggle Logic
    current = folder.get("user_allow", [])
    if permission in current:
        current.remove(permission)
    else:
        current.append(permission)
    
    folder["user_allow"] = current
    temp_data[user_id] = folder
    save_json_file(temp_file, temp_data)

    # Buttons Logic
    def btn(name, perm):
        mark = "✅" if perm in current else "❌"
        return InlineKeyboardButton(f"{name} {mark}", callback_data=f"toggle:{perm}")

    buttons = [
        [btn("➕ Add File", "add_file"), btn("📁 Add Folder", "add_folder")],
        [btn("🔗 Add URL", "add_url"), btn("🧩 Add WebApp", "add_webapp")],
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm_folder")]
    ]
    
    # यहाँ keyboard एक Object है
    keyboard = InlineKeyboardMarkup(buttons)

    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    message_id = cq.get("message", {}).get("message_id")

    # ---------------------------------------------------------
    # 👇 यहाँ है असली सुधार (The Fix)
    # ---------------------------------------------------------
    edit_message_text(
        bot_token,
        chat_id,
        message_id,
        esc("✅ Selection Updated!\nToggle options below, then click Confirm to save."),
        # keyboard ऑब्जेक्ट को Dictionary में बदलें
        reply_markup=keyboard.to_dict() 
    )

    
@on_callback_query(filters.callback_data("^confirm_folder$"))
def confirm_and_save_folder(bot_token, update, cq):
    user_id = str(cq["from"]["id"])
    callback_id = cq.get("id")
    bot_id = bot_token.split(":")[0]
    data_file_path=get_data_file(bot_token)
    temp_file = get_temp_folder(bot_token)
    temp_data = load_json_file(temp_file)
    folder_data = temp_data.get(user_id)
    if not folder_data:
        return answer_callback_query(bot_token, callback_id, "❌ Temp folder missing.", show_alert=True)
    parent_id = folder_data["parent_id"]
    if (not is_user_action_allowed(parent_id, "add_folder", bot_token) and
        int(user_id) not in ADMINS(bot_id) and
        get_created_by_from_folder(bot_token,parent_id) != int(user_id)):
        return answer_callback_query(bot_token, callback_id, "❌ You are not allowed to add a folder in this folder.", show_alert=True)
    bot_data = load_json_file(data_file_path)
    if not bot_data:
        return answer_callback_query(bot_token, callback_id, "❌ bot_data.json missing.", show_alert=True)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, parent_id)
    if not parent:
        return answer_callback_query(bot_token, callback_id, "❌ Parent folder not found.", show_alert=True)
    existing = parent.get("items", [])
    total = len(existing)
    row = total+1
    col = 0

    new_item = {
        "id": f"item_{uuid.uuid4().hex[:6]}",
        "name": folder_data["name"],
        "description": folder_data["description"],
        "type": "folder",
        "created_by": int(user_id),
        "parent_id": parent_id,
        "user_allow": folder_data.get("user_allow", []),
        "items": [],
        "row": row,
        "column": col
    }
    parent.setdefault("items", []).append(new_item)
    save_json_file(data_file_path, bot_data)
    temp_data.pop(user_id, None)
    save_json_file(temp_file, temp_data)

    status_file = get_status_file(bot_token)
    status_data = load_json_file(status_file)
    status_data.pop(user_id, None)
    save_json_file(status_file, status_data)
    git_data_file= f"BOT_DATA/{bot_id}/bot_data.json"
    save_json_to_alt_github(data_file_path,git_data_file)
    kb = generate_folder_keyboard(parent, int(user_id), bot_id)

    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    message_id = cq.get("message", {}).get("message_id")
    txt = (
        f"{esc('✅ Folder ')}"
        f"*{esc(new_item['name'])}* "
        f"{esc('saved successfully!')}"
    )
    edit_message_text(
        bot_token,
        chat_id,
        message_id,
        txt,
        reply_markup=kb
    )
    answer_callback_query(bot_token, callback_id)
@on_callback_query(filters.callback_data("^add_url:"))
def add_url_callback(bot_token, update, cq):
    folder_id = cq.get("data", "").split(":")[1]
    user_id = str(cq["from"]["id"])
    callback_id = cq.get("id")
    bot_id = bot_token.split(":")[0]

    # Permission check
    if (not is_user_action_allowed(folder_id, "add_url", bot_token) and
        int(user_id) not in ADMINS(bot_id) and
        get_created_by_from_folder(bot_token,folder_id) != int(user_id)):
        return answer_callback_query(bot_token, callback_id, "❌ You are not allowed to add a URL in this folder.", show_alert=True)
    status_data = load_json_file(get_status_file(bot_token))
    if status_data is None:
        status_data = {}

    status_data[user_id] = f"getting_url_name:{folder_id}"
    save_json_file(get_status_file(bot_token), status_data)
    temp_data = load_json_file(get_temp_url_file(bot_token))
    if temp_data is None:
        temp_data = {}

    temp_data[user_id] = {"folder_id": folder_id}
    save_json_file(get_temp_url_file(bot_token), temp_data)
    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    message_id = cq.get("message", {}).get("message_id")
    msg_text = esc('Please send a title for your URL (Example: "Click Here")')
    edit_message_text(bot_token, chat_id, message_id, msg_text)
    answer_callback_query(bot_token, callback_id)
    
@on_message(filters.private() & filters.text() & StatusFilter("getting_url_name:"))
def receive_url_name(bot_token, update, msg):
    user_id = str(msg["from"]["id"])
    url_name = msg.get("text", "").strip()
    temp_data = load_json_file(get_temp_url_file(bot_token))
    if temp_data is None:
        temp_data = {}
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["name"] = url_name
    save_json_file(get_temp_url_file(bot_token), temp_data)
    status_data = load_json_file(get_status_file(bot_token))
    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_url:{folder_id}"
    save_json_file(get_status_file(bot_token), status_data)
    chat_id = msg["chat"]["id"]
    msg_text = (
    f"{esc('Now send a valid URL (Example: https://...)')}")
    send_message(bot_token, chat_id, msg_text)

def get_owner_id(bot_token: str) -> str:
    bot_id = bot_token.split(":")[0]
    file_path = f"{BASE_PATH}/BOT_DATA/{bot_id}/ADMINS.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            owner_ids = data.get("owner", [])
            if not owner_ids:
                return None
            return owner_ids[0]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None    
@on_message(filters.private() & filters.text() & StatusFilter("getting_url:"))
def receive_url(bot_token, update, msg):
    user_id = str(msg["from"]["id"])
    url = msg.get("text", "").strip()

    # ---------------------------
    # Optional: check URL by sending button to admin
    # ---------------------------
    keyboard = [[{"text": "🌐 Checking url", "url": url}]]
    try:
        msg_text = (f"{esc('This is just a checking URL button!')}\n" 
        f"{esc('Please ignore it')}")
        send_with_error_message(
    bot_token,
    int(get_owner_id(bot_token)),
    msg_text,
    reply_markup={"inline_keyboard": keyboard})
    except Exception:
        chat_id = msg["chat"]["id"]
        msg_text = (
    f"{esc('❌ Please send a valid and reachable URL.')}")
        send_message(
    bot_token,
    chat_id,
    msg_text)
        return

    # ---------------------------
    # Save URL to temp
    # ---------------------------
    temp_data = load_json_file(get_temp_url_file(bot_token)) or {}
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["url"] = url
    save_json_file(get_temp_url_file(bot_token), temp_data)

    # ---------------------------
    # Update status
    # ---------------------------
    status_data = load_json_file(get_status_file(bot_token)) or {}
    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_caption_url:{folder_id}"
    save_json_file(get_status_file(bot_token), status_data)

    # ---------------------------
    # Prompt user for caption
    # ---------------------------
    chat_id = msg["chat"]["id"]
    msg_text = (
    f"{esc('Now send a caption for your URL :')}\n"
    f"{esc(url)}\n"
    f"{esc('(Example: This is a demo caption)')}")
    send_message(
    bot_token,
    chat_id,
    msg_text)
    
@on_message(filters.private() & filters.text() & StatusFilter("getting_caption_url:"))
def receive_url_caption(bot_token, update, msg):
    user_id = str(msg["from"]["id"])
    text = msg.get("text", "").strip()
    caption = get_markdown(msg)  # framework function
    data_file_path=get_data_file(bot_token)
    bot_id= bot_token.split(":")[0]
    # ---------------------------
    # Load temp URL data
    # ---------------------------
    temp_data = load_json_file(get_temp_url_file(bot_token)) or {}
    url_data = temp_data.get(user_id, {})
    url_data["caption"] = caption
    folder_id = url_data.get("folder_id")

    # ---------------------------
    # Load bot_data.json
    # ---------------------------
    bot_data = load_json_file(data_file_path) or {}
    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)

    if not parent:
        chat_id = msg["chat"]["id"]
        send_message(
        bot_token,
        chat_id,
        (
            f"{esc('❌ Parent folder  not found!')}"
        )
    )
        return
    existing_items = parent.get("items", [])
    max_row = max([item.get("row", 0) for item in existing_items], default=-1)

    new_item = {
        "id": f"url_{uuid.uuid4().hex[:12]}",
        "type": "url",
        "name": url_data["name"],
        "url": url_data["url"],
        "caption": caption,
        "created_by": int(user_id),
        "row": max_row + 1,
        "column": 0
    }

    parent.setdefault("items", []).append(new_item)
    save_json_file(data_file_path, bot_data)

    # ---------------------------
    # Clean temp and status
    # ---------------------------
    temp_data.pop(user_id, None)
    save_json_file(get_temp_url_file(bot_token), temp_data)

    status_data = load_json_file(get_status_file(bot_token)) or {}
    status_data.pop(user_id, None)
    save_json_file(get_status_file(bot_token), status_data)
    git_data_file= f"BOT_DATA/{bot_id}/bot_data.json"
    save_json_to_alt_github(data_file_path,git_data_file)

    # ---------------------------

    kb = generate_folder_keyboard(parent, int(user_id), bot_token)
    chat_id = msg["chat"]["id"]
    msg_text = (
        f"{esc('🔗 URL Added Successfully✅️')}"
    )
    send_message(
        bot_token,
        chat_id,
        msg_text,
        reply_markup=kb
    )
@on_callback_query(filters.callback_data(r"^edit_menu:"))
def edit_menu_handler(bot_token, update, callback_query):
    folder_id = callback_query["data"].split(":")[1]
    user_id = callback_query["from"]["id"]
    data_file_path=get_data_file(bot_token)
    data = load_json_file(data_file_path)
    bot_id = bot_token.split(":")[0]
    if not data:
        answer_callback_query(bot_token, callback_query["id"], "❌ Data file missing", show_alert=True)
        return
    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None
    root = data.get("data", {})
    folder = find_folder(root, folder_id)
    if not folder:
        answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found", show_alert=True)
        return
    if user_id not in ADMINS(bot_id) and folder.get("created_by") != user_id:
        answer_callback_query(bot_token, callback_query["id"], "❌ Not allowed", show_alert=True)
        return
    buttons = []
    for item in folder.get("items", []):
        name = item.get("name", "❓")
        item_id = item.get("id")
        buttons.append([{"text": f"✏️ {name}", "callback_data": f"edit_item:{folder_id}:{item_id}"}])
    buttons.append([{"text": "🔙Back", "callback_data": f"edit1_item1:{folder_id}"}])
    edit_message_text(
        bot_token,
        chat_id=callback_query["message"]["chat"]["id"],
        message_id=callback_query["message"]["message_id"],
        text = (
    f"{esc('🛠 Select an item to edit:')}\n\n"
    f"{esc('Please send a /update command to save data after you edits.')}"
),
        reply_markup={"inline_keyboard": buttons}
    )

@on_callback_query(filters.callback_data("^edit_item:"))
def edit_item_handler(bot_token, update, callback_query):
    _, folder_id, item_id = callback_query["data"].split(":")
    user_id = callback_query["from"]["id"]
    data_file_path=get_data_file(bot_token)
    data = load_json_file(data_file_path)
    bot_id = bot_token.split(":")[0]
    if not data:
        answer_callback_query(bot_token, callback_query["id"], "❌ Data missing", show_alert=True)
        return

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(data.get("data", {}), folder_id)
    if not folder:
        answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found", show_alert=True)
        return

    # 🔎 Find the item
    item = next((i for i in folder.get("items", []) if i["id"] == item_id), None)
    if not item:
        answer_callback_query(bot_token, callback_query["id"], "❌ Item not found", show_alert=True)
        return

    # 🔐 Access Check
    if user_id not in ADMINS(bot_id) and item.get("created_by") != user_id:
        answer_callback_query(bot_token, callback_query["id"], "❌ Not allowed", show_alert=True)
        return

    # 🧰 Options
    buttons = [
        [{"text": "✏️ Rename", "callback_data": f"rename:{folder_id}:{item_id}"}],
        [{"text": "🔀 Move", "callback_data": f"move_menu:{folder_id}:{item_id}"}],
        [{"text": "📄 Copy", "callback_data": f"copy_item:{folder_id}:{item_id}"}],
        [{"text": "🗑 Delete", "callback_data": f"delete:{folder_id}:{item_id}"}],
        [{"text": "🔙Back", "callback_data": f"edit_menu:{folder_id}"}]
    ]

    edit_message_text(
        bot_token,
        chat_id=callback_query["message"]["chat"]["id"],
        message_id=callback_query["message"]["message_id"],
        text = (
    f"{esc('Edit Options for:')} {esc(item.get('name', 'Unnamed'))}\n\n"
    f"{esc('Please send a /update command to save data after you edits.')}"
),
        reply_markup={"inline_keyboard": buttons}
    )


# =============================
# 🔙 Back to Folder Edit Root
# =============================
@on_callback_query(filters.callback_data("^edit1_item1:"))
def edit1_item1_handler(bot_token, update, callback_query):
    folder_id = callback_query["data"].split(":")[1]
    data_file_path=get_data_file(bot_token)
    data = load_json_file(data_file_path)
    if not data:
        answer_callback_query(bot_token, callback_query["id"], "❌ Data missing", show_alert=True)
        return

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(data.get("data", {}), folder_id)
    if not folder:
        answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found", show_alert=True)
        return

    default_item = next(
        (item for item in folder.get("items", []) if item.get("row") == 0 and item.get("column") == 0),
        None
    )

    if not default_item:
        buttons = [
            [
                {"text": "✏️ Edit Items", "callback_data": f"edit_menu:{folder_id}"},
                {"text": "📝 Description", "callback_data": f"update_description:{folder_id}"}
            ],
            [{"text": "🔻Edit Allow", "callback_data": f"update_folder_allow:{folder_id}"}],
            [{"text": "👑 Take Ownership", "callback_data": f"update_created_by:{folder_id}"}],
            [{"text": "🔙Back", "callback_data": f"open:{folder_id}"}]
        ]
    else:
        item_id = default_item["id"]
        buttons = [
            [
                {"text": "✏️ Edit Items", "callback_data": f"edit_menu:{folder_id}"},
                {"text": "📝 Description", "callback_data": f"update_description:{folder_id}"}
            ],
            [
                {"text": "🔀 Move", "callback_data": f"move_menu:{folder_id}:{item_id}"},
                {"text": "🔻Edit Allow", "callback_data": f"update_folder_allow:{folder_id}"}
            ],
            [{"text": "👑 Take Ownership", "callback_data": f"update_created_by:{folder_id}"}],
            [{"text": "🔙Back", "callback_data": f"open:{folder_id}"}]
        ]

    edit_message_text(
        bot_token,
        chat_id=callback_query["message"]["chat"]["id"],
        message_id=callback_query["message"]["message_id"],
        text = (
    f"{esc('🛠 What would you like to do?')}\n\n"
    f"{esc('Please send a /update command to save data after you edits.')}"
),
        reply_markup={"inline_keyboard": buttons}
    )
#@on_callback_query(filters.callback_data("^edit1_item1:"))    
@on_callback_query(filters.callback_data("^update_created_by:"))
def update_created_by_handler(bot_token, update, callback_query):
    # 🔹 Basic extraction
    print(update)
    data = callback_query.get("data", "")
    user = callback_query.get("from", {})
    user_id = user.get("id")
    message = callback_query.get("message", {})
    bot_id = bot_token.split(":")[0]
    parts = data.split(":")
    print(parts)
    if len(parts) < 2:
        print("❌ Invalid callback data.")
        answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)
        return

    folder_id = parts[1]
    print(folder_id)

    # ✅ Access Check (Admins only)
    admins = ADMINS(bot_id)
    if user_id not in admins:
        answer_callback_query(bot_token, callback_query["id"], "❌ Only admins can change ownership.", True)
        print("❌ Only admins can change ownership.")
        return

    # 🔄 Load bot_data.json (bot-specific)
    print("I am working")
    data_file = get_data_file(bot_token)
    try:
        with open(data_file, "r") as f:
            data_json = json.load(f)
    except:
        answer_callback_query(bot_token, callback_query["id"], "❌ Failed to load bot_data.json", True)
        return

    # 🔍 Recursive folder finder
    def find_folder(folder):
        if folder.get("id") == folder_id:
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                result = find_folder(item)
                if result:
                    return result
        return None

    root = data_json.get("data", {})
    folder = find_folder(root)
    print("I am working")
    if not folder:
        answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found.", True)
        return

    # ✏️ Update created_by
    folder["created_by"] = user_id

    # 💾 Save back
    with open(data_file, "w") as f:
        json.dump(data_json, f, indent=2)

    # ✅ Success message
    answer_callback_query(bot_token, callback_query["id"], "✅ Ownership updated successfully.\n\nPlease send a /update command to save data after you edits.", True)
    print("Transfered")

    # 🔘 Updated folder view
    kb = generate_folder_keyboard(folder, user_id, bot_id)

    # 📝 Edit existing message text
    edit_message_text(
        bot_token,
        chat_id=message["chat"]["id"],
        message_id=message["message_id"],
        text = (
    f"{esc('🆕 This folder is now owned by you (User ID:')} `{esc(user_id)}`)"
),
        reply_markup=kb
    )
@on_callback_query(filters.callback_data("^update_description:"))
def update_description_prompt(bot_token, update, query):
    # 1. Spinner सबसे पहले रोकें
    callback_id = query.get("id")
    answer_callback_query(bot_token, callback_id)

    data = query.get("data", "")
    folder_id = data.split(":")[1] if ":" in data else None
    user_id = str(query.get("from", {}).get("id"))
    
    # Message Details
    message = query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    if not folder_id or not user_id:
        # अगर डेटा गलत है (Alert दिखाएं)
        answer_callback_query(bot_token, callback_id, text="❌ Invalid Data", show_alert=True)
        return

    # 2. Status अपडेट करें (Helpers का उपयोग करके)
    status_file = get_status_file(bot_token)
    status_data = load_json_file(status_file)
    
    status_data[user_id] = f"updating_description:{folder_id}"
    save_json_file(status_file, status_data)

    # 3. डेटा लोड करें और फोल्डर ढूंढें
    data_file = get_data_file(bot_token)
    full_data = load_json_file(data_file)
    
    if not full_data:
        answer_callback_query(bot_token, callback_id, text="❌ Data file not found!", show_alert=True)
        return

    # Recursive Function to find folder
    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(full_data.get("data", {}), folder_id)
    if not folder:
        answer_callback_query(bot_token, callback_id, text="❌ Folder not found!", show_alert=True)
        return

    current_description = folder.get("description", "No Description")
    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel / Back", callback_data=f"open:{folder_id}")]
    ])
    text = (
        f"{esc('✍️ Please send the new description for this folder.')}\n\n"
        f"*{esc('Current Description:')}*\n"
        f"{current_description}\n\n"
        f"{esc('You can use Markdown (Bold, Italic, Links).')}\n"
        f"{esc('Send text or Click Cancel.')}"
    )

    try:
        edit_message_text(
            bot_token,
            chat_id,
            message_id,
            text
        )
    except Exception as e:
        print(f"Error updating prompt: {e}")

@on_message(filters.private() & filters.text() & StatusFilter("updating_description"))
def receive_new_description(bot_token, update, msg):
    user_id = str(msg["from"]["id"])
    text = msg.get("text", "").strip()
    bot_id = bot_token.split(":")[0]

    # 🔄 Paths based on bot_token
    data_file = get_data_file(bot_token)
    status_user_file = get_status_file(bot_token)

    # 📦 Load status
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_value = status_data.get(user_id, "")
    if ":" not in status_value:
        send_message(
        bot_token,
        user_id,
        (
            f"{esc('❌ Invalid folder status.')}"
        )
    )
        return

    folder_id = status_value.split(":", 1)[1]

    # 📂 Load bot_data
    try:
        with open(data_file, "r") as f:
            bot_data = json.load(f)
    except:
        send_message(bot_token, user_id, "❌ bot_data.json not found.")
        return

    # 🔍 Folder finder
    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        send_message(bot_token, user_id, "❌ Folder not found.")
        return

    # 📝 Markdown escape
    formatted = get_markdown(msg)
    folder["description"] = formatted
    with open(data_file, "w") as f:
        json.dump(bot_data, f, indent=2)
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)
    kb = generate_folder_keyboard(folder, int(user_id), bot_id)
    send_message(
        bot_token,
        user_id,
        (
            f"📝 *{esc('Description updated successfully!')}*\n\n"
            f"{formatted}\n\n"
            f"{esc('Please send a /update command to save data after you edits.')}"
        ),
        reply_markup=kb
    )

@on_callback_query(filters.callback_data("^rename:"))
def rename_item_callback(bot_token, update, callback_query):
    data = callback_query.get("data", "")
    parts = data.split(":")
    if len(parts) < 3:
        answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)
        return

    folder_id, item_id = parts[1:]
    user = callback_query.get("from", {})
    user_id = str(user.get("id"))
    message = callback_query.get("message", {})

    # 🔄 Save user status
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = f"renaming:{folder_id}:{item_id}"
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # 🔍 Find current item
    data_file = get_data_file(bot_token)
    try:
        with open(data_file, "r") as f:
            bot_data = json.load(f)
    except:
        answer_callback_query(bot_token, callback_query["id"], "❌ Failed to load bot data.", True)
        return

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for i in folder.get("items", []):
            if i.get("type") == "folder":
                found = find_folder(i, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found.", True)
        return

    item = next((i for i in folder.get("items", []) if i.get("id") == item_id), None)
    if not item:
        answer_callback_query(bot_token, callback_query["id"], "❌ Item not found.", True)
        return
    current_name = item.get("name", "Unnamed")
    edit_message_text(
        bot_token,
        chat_id=message["chat"]["id"],
        message_id=message["message_id"],
        text=(
            f"{esc('📝 Please send the new name for this item.')}\n\n"
            f"📄 *{esc('Current Name')}*:\n"
            f"`{esc(current_name)}`\n\n"
            f"{esc('Please send a /update command to save data after you edits.')}"
        )
    )

@on_message(filters.private() & filters.text() & StatusFilter("renaming:"))
def rename_text_handler(bot_token, update, msg):
    user = msg.get("from", {})
    user_id = str(user.get("id"))
    new_name = msg.get("text", "").strip()
    bot_id = bot_token.split(":")[0]

    # 🔄 Load status
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status = status_data.get(user_id, "")
    parts = status.split(":")
    if len(parts) != 3:
        send_message(bot_token, user_id, "❌ Status error.")
        return

    _, folder_id, item_id = parts

    # 🔍 Load bot data
    data_file = get_data_file(bot_token)
    try:
        with open(data_file, "r") as f:
            bot_data = json.load(f)
    except:
        send_message(bot_token, user_id, "❌ Failed to load bot data.")
        return

    def find_folder(folder, fid):
        if folder.get("id") == fid:
            return folder
        for i in folder.get("items", []):
            if i.get("type") == "folder":
                found = find_folder(i, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        send_message(bot_token, user_id, "❌ Folder not found.")
        return

    item = next((i for i in folder.get("items", []) if i.get("id") == item_id), None)
    if not item:
        send_message(bot_token, user_id, "❌ Item not found.")
        return

    # 🔤 Update name
    item["name"] = new_name

    with open(data_file, "w") as f:
        json.dump(bot_data, f, indent=2)

    # 🧹 Clear status
    status_data.pop(user_id, None)
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    kb = generate_folder_keyboard(folder, int(user_id), bot_id)
    send_message(
        bot_token,
        user_id,
        (
            f"{esc('✅ Name Renamed')}\n\n"
            f"{esc('Please send a /update command to save data after you edits.')}"
        ),
        reply_markup=kb
    )

@on_callback_query(filters.callback_data("^delete:"))
def delete_item_confirm(bot_token, update, callback_query):
    data = callback_query.get("data", "")
    parts = data.split(":")
    if len(parts) < 3:
        answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)
        return
    folder_id, item_id = parts[1:]
    user = callback_query.get("from", {})
    user_id = str(user.get("id"))
    message = callback_query.get("message", {})
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}
    status_data[user_id] = f"deleting:{folder_id}:{item_id}"
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)
    edit_message_text(
        bot_token,
        chat_id=message["chat"]["id"],
        message_id=message["message_id"],
        text=(
            f"{esc('❗ To delete this item, please send the folder ID:')}\n\n"
            f"🔐 `{esc(folder_id)}`\n\n"
            f"{esc('⚠️ Warning: Once deleted, this item **CANNOT be restored**. Proceed with caution.')}"
        )
    )


@on_message(filters.private() & filters.text() & StatusFilter("deleting"))
def delete_item_final(bot_token, update, msg):
    user = msg.get("from", {})
    user_id = str(user.get("id"))
    entered_text = msg.get("text", "").strip()
    bot_id = bot_token.split(":")[0]

    # 🔄 Load status
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status = status_data.get(user_id, "")
    parts = status.split(":")
    if len(parts) != 3:
        send_message(
        bot_token,
        user_id,
        (
            f"{esc('❌ Invalid status.')}"
        )
    )
        return

    _, folder_id, item_id = parts

    # ❌ Compare folder ID
    if entered_text != folder_id:
        status_data.pop(user_id, None)
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
        send_message(
        bot_token,
        user_id,
        (
            f"{esc('❌ File deleting canceled due to wrong folder ID!')}"
        )
    )
        return

    # 🔍 Load main data
    data_file = get_data_file(bot_token)
    try:
        with open(data_file, "r") as f:
            bot_data = json.load(f)
    except:
        send_message(
        bot_token,
        user_id,
        (
            f"{esc('❌ Failed to load bot data.')}"
        )
    )
        return

    def find_folder(folder, fid):
        if folder.get("id") == fid:
            return folder
        for i in folder.get("items", []):
            if i.get("type") == "folder":
                found = find_folder(i, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        send_message(
        bot_token,
        user_id,
        (
            f"{esc('❌ Folder not found.')}"
        )
    )
        return

    # 🗑 Remove the item
    folder["items"] = [i for i in folder.get("items", []) if i.get("id") != item_id]

    # 💾 Save updated bot data
    with open(data_file, "w") as f:
        json.dump(bot_data, f, indent=2)

    # 🧹 Clear status
    status_data.pop(user_id, None)
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    kb = generate_folder_keyboard(folder, int(user_id), bot_id)
    send_message(
        bot_token,
        user_id,
        (
            f"{esc('✅ Item deleted')}\n\n"
            f"{esc('Please send a /update command to save data after you edits.')}"
        ),
        reply_markup=kb
    )
  
@on_callback_query(filters.callback_data("^move_menu:"))
def move_menu_handler(bot_token, update, callback_query):
    callback_id = callback_query.get("id")
    
    # 1. सबसे पहले Spinner रोकें
    answer_callback_query(bot_token, callback_id)

    data = callback_query.get("data", "")
    parts = data.split(":")
    if len(parts) < 3:
        # अगर डेटा गलत है तो बस रिटर्न कर दें
        return

    folder_id, item_id = parts[1:]
    user = callback_query.get("from", {})
    user_id = user.get("id")
    message = callback_query.get("message", {})
    bot_id = bot_token.split(":")[0]

    # 🔐 Access check
    # (ADMINS logic wahi rahega)
    # yahan assume kar rahe hain ki aapke paas get_created_by... function hai
    
    # 🔄 Load bot data
    data_file = get_data_file(bot_token)
    try:
        data_json = load_json_file(data_file) # agar helper function hai to wahi use karein
    except:
        return

    # 🔍 Find folder recursively
    def find_folder(folder, fid):
        if folder.get("id") == fid:
            return folder
        for i in folder.get("items", []):
            if i.get("type") == "folder":
                found = find_folder(i, fid)
                if found:
                    return found
        return None

    folder = find_folder(data_json.get("data", {}), folder_id)
    if not folder:
        answer_callback_query(bot_token, callback_id, text="❌ Folder not found.", show_alert=True)
        return

    # 🔎 Validate selected item
    items_list = folder.get("items", [])
    item_ids = [i.get("id") for i in items_list]
    
    if item_id not in item_ids:
        answer_callback_query(bot_token, callback_id, text="❌ Item not found.", show_alert=True)
        return

    # 🧩 Build layout grid
    # defaultdict ka use nahi kar rahe to simple dict se banayenge (safe side)
    layout = {} 
    
    for i in items_list:
        r, c = i.get("row", 0), i.get("column", 0)
        
        # Icons logic
        i_type = i.get("type", "file")
        if i_type == "folder": icon_char = "📁"
        elif i_type == "url": icon_char = "🔗"
        elif i_type == "webapp": icon_char = "🧩"
        else: icon_char = "📄"
            
        # Highlight Selected Item
        if i.get("id") == item_id:
            # Selected item ke liye 'ignore' callback (taki click na ho)
            btn = InlineKeyboardButton(f"♻️ {i.get('name')}", callback_data="ignore")
        else:
            # Dusre items par click karne se wo select ho jayenge (move_menu call hoga)
            btn = InlineKeyboardButton(f"{icon_char} {i.get('name')}", callback_data=f"move_menu:{folder_id}:{i.get('id')}")
        
        if r not in layout: layout[r] = {}
        layout[r][c] = btn

    # 🏗 Build grid form dict
    grid = []
    for r in sorted(layout.keys()):
        row_buttons = [layout[r][c] for c in sorted(layout[r].keys())]
        grid.append(row_buttons)

    # ⬅️⬆️⬇️➡️ Movement buttons
    # Note: Callback data 'move_item' logic par depend karega jo aapne banaya hoga
    move_row = [
        InlineKeyboardButton("⬅️", callback_data=f"move_left:{folder_id}:{item_id}"),
        InlineKeyboardButton("⬆️", callback_data=f"move_up:{folder_id}:{item_id}"),
        InlineKeyboardButton("⬇️", callback_data=f"move_down:{folder_id}:{item_id}"),
        InlineKeyboardButton("➡️", callback_data=f"move_right:{folder_id}:{item_id}"),
    ]
    grid.append(move_row)

    # 🔙 Back/DONE button
    grid.append([InlineKeyboardButton("DONE✔️", callback_data=f"edit1_item1:{folder_id}")])

    keyboard = InlineKeyboardMarkup(grid)

    # ✏️ Edit message
    # Text ko esc() me daalna zaruri hai kyunki MarkdownV2 hai
    try:
        edit_message_text(
            bot_token,
            chat_id=message["chat"]["id"],
            message_id=message["message_id"],
            text=(
                f"{esc('🔄 Move the selected item (♻️):')}\n\n"
                f"{esc('Use arrows to move. Click DONE when finished.')}"
            ),
            # 👇 SABSE IMPORT ANT FIX YAHAN HAI:
            reply_markup=keyboard.to_dict() if hasattr(keyboard, "to_dict") else keyboard
        )
    except Exception as e:
        print(f"Move menu error: {e}")

def load_data(bot_token):
    data_file = get_data_file(bot_token)
    with open(data_file, "r") as f:
        return json.load(f)

def save_data(data, bot_token):
    data_file = get_data_file(bot_token)
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)
def compact_items(items):
    # Row और column के अनुसार sort
    items = sorted(items, key=lambda x: (x["row"], x["column"]))
    new_items = []
    row_map = {}
    row_counter = 0

    # Unique row नंबर को 0,1,2... में remap करो
    for row in sorted(set(i["row"] for i in items)):
        row_map[row] = row_counter
        row_counter += 1

    for item in items:
        item["row"] = row_map[item["row"]]
        new_items.append(item)

    # Final sorted compact list वापस भेजो
    return sorted(new_items, key=lambda x: (x["row"], x["column"]))

@on_callback_query(filters.callback_data("^move_up:"))
def move_up_handler(bot_token, update, callback_query):
    data_str = callback_query.get("data", "")
    parts = data_str.split(":")
    if len(parts) < 3:
        return answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)

    folder_id, item_id = parts[1:]
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    try:
        # 🔄 Load data
        data_file = get_data_file(bot_token)
        with open(data_file, "r") as f:
            data = json.load(f)

        def find_folder(folder, fid):
            if folder.get("id") == fid:
                return folder
            for i in folder.get("items", []):
                if i.get("type") == "folder":
                    found = find_folder(i, fid)
                    if found:
                        return found
            return None

        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found!", True)

        items = folder.get("items", [])
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Item not found!", True)

        current_row = item.get("row", 0)
        current_col = item.get("column", 0)

        same_row_items = [i for i in items if i.get("row") == current_row and i.get("id") != item_id]

        if same_row_items:
            # बाकियों को push नीचे
            for i in items:
                if i.get("id") != item_id and i.get("row", 0) >= current_row:
                    i["row"] += 1
            item["column"] = 0

            # Column conflict avoid
            by_position = {}
            for i in items:
                key = (i["row"], i["column"])
                while key in by_position:
                    i["column"] += 1
                    key = (i["row"], i["column"])
                by_position[key] = i["id"]

        else:
            if current_row > 0:
                # ऊपर वाली row में shift
                above_items = [i for i in items if i.get("row", 0) == current_row - 1]
                existing_cols = [i.get("column", 0) for i in above_items]
                item["row"] = current_row - 1
                item["column"] = max(existing_cols, default=-1) + 1
            else:
                # row == 0 और अकेला
                max_row = max((i.get("row", 0) for i in items if i.get("id") != item_id), default=0)
                old_row = item.get("row", 0)
                item["row"] = max_row + 1
                item["column"] = 0

                # ऊपर वालों को -1 करो
                for i in items:
                    if i.get("id") != item_id and i.get("row", 0) < old_row:
                        i["row"] -= 1

        # 🔄 Compact final layout
        folder["items"] = compact_items(items)

        # 💾 Save
        save_data(data, bot_token)

        # 🔁 Call move_menu again to refresh
        callback_query["data"] = f"move_menu:{folder_id}:{item_id}"
        move_menu_handler(bot_token, update, callback_query)

    except Exception as e:
        answer_callback_query(bot_token, callback_query["id"], "⚠️ Please Try Again!", True)

@on_callback_query(filters.callback_data("^move_down:"))
def move_down_handler(bot_token, update, callback_query):
    data_str = callback_query.get("data", "")
    parts = data_str.split(":")
    if len(parts) < 3:
        return answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)

    folder_id, item_id = parts[1:]
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    try:
        # 🔄 Load bot data
        data_file = get_data_file(bot_token)
        with open(data_file, "r") as f:
            data = json.load(f)

        def find_folder(folder, fid):
            if folder.get("id") == fid:
                return folder
            for i in folder.get("items", []):
                if i.get("type") == "folder":
                    found = find_folder(i, fid)
                    if found:
                        return found
            return None

        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found!", True)

        items = folder.get("items", [])
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Item not found!", True)

        current_row = item.get("row", 0)
        current_col = item.get("column", 0)

        same_row_others = [i for i in items if i.get("row", 0) == current_row and i.get("id") != item_id]
        max_row = max([i.get("row", 0) for i in items], default=0)

        if same_row_others:
            # ✅ Same row में और items हैं
            for i in items:
                if i.get("row", 0) > current_row:
                    i["row"] += 1  # नीचे की rows shift

            item["row"] = current_row + 1
            item["column"] = 0  # नीचे नई row की col 0

            if current_col == 0:
                for i in items:
                    if i.get("row", 0) == current_row and i.get("column", 0) > 0:
                        i["column"] -= 1
        else:
            # ✅ अकेला row में
            if current_row < max_row:
                below_items = [i for i in items if i.get("row", 0) == current_row + 1]
                cols = [i.get("column", 0) for i in below_items]
                item["row"] = current_row + 1
                item["column"] = max(cols, default=-1) + 1
            else:
                # ✅ already last row
                for i in items:
                    if i.get("id") != item_id:
                        i["row"] += 1
                item["row"] = 0
                item["column"] = 0

        # 🔄 Compact layout
        folder["items"] = compact_items(items)

        # 💾 Save
        save_data(data, bot_token)

        # 🔁 Refresh menu
        callback_query["data"] = f"move_menu:{folder_id}:{item_id}"
        move_menu_handler(bot_token, update, callback_query)

    except Exception as e:
        answer_callback_query(bot_token, callback_query["id"], "⚠️ Please Try Again!", True)
  
@on_callback_query(filters.callback_data("^move_left"))
def move_left_handler(bot_token, update, callback_query):
    data_str = callback_query.get("data", "")
    parts = data_str.split(":")
    if len(parts) < 3:
        return answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)

    folder_id, item_id = parts[1:]
    try:
        # Load bot data
        data_file = get_data_file(bot_token)
        with open(data_file, "r") as f:
            data = json.load(f)

        def find_folder(folder, fid):
            if folder.get("id") == fid:
                return folder
            for i in folder.get("items", []):
                if i.get("type") == "folder":
                    found = find_folder(i, fid)
                    if found:
                        return found
            return None

        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Folder Not Found!", True)

        items = folder.get("items", [])
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            return answer_callback_query(bot_token, callback_query["id"], "❌ No Item Found!", True)

        row = item.get("row", 0)
        col = item.get("column", 0)

        if col == 0:
            return answer_callback_query(bot_token, callback_query["id"], "❌ No Space on the left", True)

        left_item = next((i for i in items if i.get("row", 0) == row and i.get("column", 0) == col - 1), None)
        if left_item:
            left_item["column"] += 1
        item["column"] -= 1

        folder["items"] = compact_items(items)
        save_data(data, bot_token)

        callback_query["data"] = f"move_menu:{folder_id}:{item_id}"
        move_menu_handler(bot_token, update, callback_query)

    except Exception:
        answer_callback_query(bot_token, callback_query["id"], "⚠️ Error: Please Try Again!", True)


@on_callback_query(filters.callback_data("^move_right"))
def move_right_handler(bot_token, update, callback_query):
    data_str = callback_query.get("data", "")
    parts = data_str.split(":")
    if len(parts) < 3:
        return answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)

    folder_id, item_id = parts[1:]
    try:
        data_file = get_data_file(bot_token)
        with open(data_file, "r") as f:
            data = json.load(f)

        def find_folder(folder, fid):
            if folder.get("id") == fid:
                return folder
            for i in folder.get("items", []):
                if i.get("type") == "folder":
                    found = find_folder(i, fid)
                    if found:
                        return found
            return None

        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Folder not found!", True)

        items = folder.get("items", [])
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            return answer_callback_query(bot_token, callback_query["id"], "❌ Item not found!", True)

        row = item.get("row", 0)
        col = item.get("column", 0)

        row_items = [i for i in items if i.get("row", 0) == row]
        max_col = max([i.get("column", 0) for i in row_items], default=0)

        if col == max_col:
            return answer_callback_query(bot_token, callback_query["id"], "❌ No space on the right", True)

        right_item = next((i for i in row_items if i.get("column", 0) == col + 1), None)
        if right_item:
            right_item["column"] -= 1
        item["column"] += 1

        folder["items"] = compact_items(items)
        save_data(data, bot_token)

        callback_query["data"] = f"move_menu:{folder_id}:{item_id}"
        move_menu_handler(bot_token, update, callback_query)

    except Exception:
        answer_callback_query(bot_token, callback_query["id"], "⚠️ Please Try Again!", True)
        
@on_callback_query(filters.callback_data("^add_webapp"))
def add_webapp_callback(bot_token, update, callback_query):
    data_str = callback_query.get("data", "")
    bot_id = bot_token.split(":")[0]
    parts = data_str.split(":")
    if len(parts) < 2:
        return answer_callback_query(bot_token, callback_query["id"], "❌ Invalid callback data.", True)

    folder_id = parts[1]
    user_id = str(callback_query["from"]["id"])

    if (not is_user_action_allowed(folder_id, "add_webapp", bot_token)
        and int(user_id) not in ADMINS(bot_id)
        and get_created_by_from_folder(bot_token, folder_id) != int(user_id)):
        return answer_callback_query(bot_token, callback_query["id"], "❌ You are not allowed to add a web app in this folder.", True)

    # 🔄 Status Set
    status_user_file = get_status_file(bot_token)
    try:
        with open(status_user_file, "r") as f:
            content = f.read().strip()
            status_data = json.loads(content) if content else {}
    except:
        status_data = {}

    status_data[user_id] = f"getting_webapp_name:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)
    temp_webapp_file = get_temp_webapp_file(bot_token)
    try:
        with open(temp_webapp_file, "r") as f:
            content = f.read().strip()
            temp_data = json.loads(content) if content else {}
    except:
        temp_data = {}
    temp_data[user_id] = {"folder_id": folder_id}
    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f, indent=2)
    edit_message_text(
        bot_token,
        callback_query["message"]["chat"]["id"],
        callback_query["message"]["message_id"],
        esc('Please send a title for your web app (Example : "OPEN WEB APP")')
        
    )


@on_message(filters.private()  & filters.text()  & StatusFilter("getting_webapp_name"))
def receive_webapp_name(bot_token, update, message):
    user_id = str(message["from"]["id"])
    webapp_name = message["text"].strip()

    temp_webapp_file = get_temp_webapp_file(bot_token)
    try:
        with open(temp_webapp_file, "r") as f:
            content = f.read().strip()
            temp_data = json.loads(content) if content else {}
    except:
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["name"] = webapp_name
    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    status_user_file = get_status_file(bot_token)
    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_webapp:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    send_message(
        bot_token,
        message["chat"]["id"],esc('Now send a url of your webapp (Example : https://...)')
    )
    
@on_message(filters.private()  & filters.text()  & StatusFilter("getting_webapp"))
def receive_webapp(bot_token, update, message):
    user_id = str(message["from"]["id"])
    webapp = message["text"].strip()

    # WebApp button preview (sent to admin or test user)
    keyboard = {
        "inline_keyboard": [[{"text": "🌐 Open WebApp", "web_app": {"url": webapp}}]]
    }

    try:
        send_with_error_message(
        bot_token,
        int(get_owner_id(bot_token)),esc('This is only url checking message! Please ignor this message.'),
        reply_markup=keyboard
    )
    except Exception:
        return send_message(
        bot_token,
        message["chat"]["id"],esc('❌ Please send a valid and reachable URL.')
    )

    # Temp storage
    temp_webapp_file = get_temp_webapp_file(bot_token)
    try:
        with open(temp_webapp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["webapp"] = webapp

    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    # Update status
    status_user_file = get_status_file(bot_token)
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_caption_webapp:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    send_message(
        bot_token,
        message["chat"]["id"],esc('Now send a caption for your Webapp.')
        )
    )


@on_message(filters.private()  & filters.text()  & StatusFilter("getting_caption_webapp"))
def receive_webapp_caption(bot_token, update, message):
    user_id = str(message["from"]["id"])
    caption = message["text"].strip()
    data_file = get_data_file(bot_token)
    bot_id = bot_token.split(":")[0]

    temp_webapp_file = get_temp_webapp_file(bot_token)
    try:
        with open(temp_webapp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    webapp_data = temp_data.get(user_id, {})
    webapp_data["caption"] = caption
    folder_id = webapp_data.get("folder_id")

    # Load main bot data
    with open(data_file, "r") as f:
        bot_data = json.load(f)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)
    if not parent:
        return send_message(
        bot_token,
        message["chat"]["id"],
        (
            f"{esc('❌ Parent folder नहीं मिला।')}"
        )
    )

    # Calculate max row
    existing_items = parent.get("items", [])
    max_row = max([item.get("row", 0) for item in existing_items], default=-1)

    # New webapp item
    new_item = {
        "id": f"webapp_{uuid.uuid4().hex[:12]}",
        "type": "webapp",
        "name": webapp_data["name"],
        "url": webapp_data["webapp"],
        "caption": caption,
        "created_by": int(user_id),
        "row": max_row + 1,
        "column": 0
    }
    parent.setdefault("items", []).append(new_item)

    with open(data_file, "w") as f:
        json.dump(bot_data, f, indent=2)

    # Cleanup temp & status
    temp_data.pop(user_id, None)
    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f)

    status_user_file = get_status_file(bot_token)
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    # Send confirmation
    chat_id = message["chat"]["id"]
    git_data_file= f"BOT_DATA/{bot_id}/bot_data.json"
    save_json_to_alt_github(data_file,git_data_file)
    #send_message(bot_token, chat_id, "🧩 WebApp सफलतापूर्वक जोड़ा गया ✅")
    kb = generate_folder_keyboard(parent, int(user_id), bot_id)
    send_message(
        bot_token,
        chat_id,
        esc('🧩 WebApp सफलतापूर्वक जोड़ा गया ✅'),
        reply_markup=kb
    )

@on_callback_query(filters.callback_data("^add_file"))
def add_file_callback(bot_token,update, callback_query):
    data = callback_query["data"]
    folder_id = data.split(":")[1]
    bot_id = bot_token.split(":")[0]
    user_id = str(callback_query["from"]["id"])

    # 🟢 Optional startup message
    #send_startup_message_once()

    # 🔒 Access Check
    if (
        not is_user_action_allowed(folder_id, "add_file", bot_token)
        and int(user_id) not in ADMINS(bot_id)
        and get_created_by_from_folder(bot_token, folder_id) != int(user_id)
    ):
        return answer_callback_query(
            bot_token,
            callback_query["id"],
            "❌ You are not allowed to add a file in this folder.",
            True,
        )

    # 🧩 Load or Initialize Status File
    status_user_file = get_status_file(bot_token)
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = f"waiting_file_doc:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # 📂 Load or Initialize Temp File JSON
    temp_file_json = get_temp_file(bot_token)
    try:
        with open(temp_file_json, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {"folder_id": folder_id, "files": {}}
    else:
        temp_data[user_id]["folder_id"] = folder_id
        temp_data[user_id].setdefault("files", {})

    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 📨 Edit message to ask user
    chat_id = callback_query["message"]["chat"]["id"]
    message_id = callback_query["message"]["message_id"]
    edit_message_text(
        bot_token,
        chat_id,
        message_id,
        esc('Please Send Document(s)..')
    )
def get_new_file_id_from_resp(resp: dict):
    # resp is Telegram API JSON response: {"ok": True, "result": { ... message ...}}
    if not resp or not resp.get("ok"):
        return None
    result = resp.get("result", {})
    # try common keys
    for key in ("document", "photo", "video", "audio", "voice"):
        if key in result:
            if key == "photo":
                # photo is list
                photos = result["photo"]
                if isinstance(photos, list) and photos:
                    return photos[-1].get("file_id")
            else:
                return result[key].get("file_id")
    # sometimes message may have 'document' nested under result.message (rare) - fallback scan
    def scan_for_file_id(obj):
        if isinstance(obj, dict):
            if "file_id" in obj:
                return obj["file_id"]
            for v in obj.values():
                found = scan_for_file_id(v)
                if found:
                    return found
        if isinstance(obj, list):
            for el in obj:
                found = scan_for_file_id(el)
                if found:
                    return found
        return None
    return scan_for_file_id(result)



def get_file_channel_id(bot_token: str) -> str:
    bot_id = bot_token.split(":")[0]
    file_path = f"{BASE_PATH}/BOT_DATA/{bot_id}/ADDITIONAL_DATA.json"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            file_channel_id = data.get("FILE_CHANNEL_ID", None)
            if file_channel_id:
              print(file_channel_id)
              return file_channel_id
            print("NON")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
        
@on_message(filters.private() & StatusFilter("waiting_file_doc") & (filters.document() | filters.photo() | filters.video() | filters.audio()))
def receive_any_media(bot_token, update, msg):
    bot_id = bot_token.split(":")[0]
    
    try:
        user_id = str(msg.get("from", {}).get("id"))
        chat_id = msg.get("chat", {}).get("id")
        if not user_id: return

        # ---------------------------
        # 1. Status & Folder Check
        # ---------------------------
        status_file = get_status_file(bot_token)
        status_data = load_json_file(status_file) # Helper use karein
        
        status_val = status_data.get(user_id, "")
        if ":" not in status_val:
            send_message(bot_token, chat_id, esc("❌ Invalid status. Please restart."))
            return
            
        folder_id = status_val.split(":", 1)[1]

        # ---------------------------
        # 2. Permission Check
        # ---------------------------
        if (not is_user_action_allowed(folder_id, "add_file", bot_token)
            and int(user_id) not in ADMINS(bot_id)
            and get_created_by_from_folder(bot_token, folder_id) != int(user_id)):
            send_message(bot_token, chat_id, esc("❌ You are not allowed to add a file in this folder."))
            return

        # ---------------------------
        # 3. Identify Media
        # ---------------------------
        media_type = None
        file_name = "Unnamed File"
        original_file_id = None

        if "document" in msg:
            media_type = "document"
            original_file_id = msg["document"]["file_id"]
            file_name = msg["document"].get("file_name") or "Document"
        elif "video" in msg:
            media_type = "video"
            original_file_id = msg["video"]["file_id"]
            file_name = msg["video"].get("file_name") or "Video"
        elif "audio" in msg:
            media_type = "audio"
            original_file_id = msg["audio"]["file_id"]
            file_name = msg["audio"].get("file_name") or "Audio"
        elif "photo" in msg:
            media_type = "photo"
            # Photo list hoti hai, last wala best quality hota hai
            original_file_id = msg["photo"][-1]["file_id"]
            file_name = "Image.jpg"

        if not original_file_id:
            send_message(bot_token, chat_id, esc("❌ Supported media not found."))
            return

        # ---------------------------
        # 4. Check DB Channel
        # ---------------------------
        FILE_LOGS = get_file_channel_id(bot_token)
        if not FILE_LOGS:
            send_message(bot_token, chat_id, esc("⚠️ Database channel not set. Please set it first via @BotixHubBot."))
            return
        try:
            if media_type == "photo":
                resp = send_photo(bot_token, FILE_LOGS, photo=original_file_id)
            elif media_type == "video":
                resp = send_video(bot_token, FILE_LOGS, video=original_file_id)
            elif media_type == "audio":
                resp = send_audio(bot_token, FILE_LOGS, audio=original_file_id)
            else:
                resp = send_document(bot_token, FILE_LOGS, document=original_file_id)
        except Exception as e:
            print(f"Log Channel Error: {e}")
            send_message(bot_token, chat_id, esc("❌ Failed to send file to Database Channel. Make sure I am Admin there."))
            return

        new_file_id = get_new_file_id_from_resp(resp)
        if not new_file_id:
            msg_err = (
                f"{esc('❌ Failed to get File ID.')}\n"
                f"{esc('Please ensure I am an Admin in the Database Channel:')}\n"
                f"`{esc(str(FILE_LOGS))}`"
            )
            send_message(bot_token, chat_id, msg_err)
            return

        # ---------------------------
        # 6. Handle Caption (The Fix)
        # ---------------------------
        # get_markdown use karein (formatted text ke liye)
        try:
            formatted_caption = get_markdown(msg)
        except Exception as e:
            print(f"Caption Error: {e}")
            formatted_caption = ""

        # Agar caption khali hai, to File Name use karein (lekin ESCAPE karke)
        if not formatted_caption or formatted_caption.strip() == "":
            formatted_caption = esc(file_name)

        final_caption = formatted_caption
        
        # ---------------------------
        # 7. Save to Temp File
        # ---------------------------
        temp_file = get_temp_file(bot_token)
        temp_data = load_json_file(temp_file)

        if user_id not in temp_data:
            temp_data[user_id] = {"folder_id": folder_id, "files": {}}

        file_uuid = uuid.uuid4().hex[:12]
        
        temp_data[user_id]["files"][file_uuid] = {
            "id": file_uuid,
            "type": "file",
            "sub_type": media_type,
            "name": file_name, # Database me raw name save karein
            "file_id": new_file_id,
            "caption": final_caption, # MarkdownV2 caption
            "visibility": "private",
            "row": 0,
            "column": 0
        }

        save_json_file(temp_file, temp_data)

        # ---------------------------
        # 8. Reply to User
        # ---------------------------
        buttons = [
            [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file:{file_uuid}")],
            [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption:{file_uuid}")],
            [InlineKeyboardButton("👁 Visibility: Public", callback_data=f"toggle_visibility:{file_uuid}")],
            [InlineKeyboardButton("FILE IS UNDER A USER", callback_data=f"add_premium_owner:{file_uuid}")],
            [
                InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file:{file_uuid}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file:{file_uuid}")
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        # Send Preview (Using Threading to be fast)
        # Important: Pass formatted=True because 'final_caption' is already escaped/formatted
        def send_preview():
            # Note: InlineKeyboardMarkup ko .to_dict() karna agar helper me handling nahi hai
            kb_dict = keyboard.to_dict() if hasattr(keyboard, "to_dict") else keyboard
            
            if media_type == "document":
                send_document(bot_token, chat_id, new_file_id, caption=final_caption, reply_markup=kb_dict)
            elif media_type == "photo":
                send_photo(bot_token, chat_id, new_file_id, caption=final_caption, reply_markup=kb_dict)
            elif media_type == "video":
                send_video(bot_token, chat_id, new_file_id, caption=final_caption, reply_markup=kb_dict)
            elif media_type == "audio":
                send_audio(bot_token, chat_id, new_file_id, caption=final_caption, reply_markup=kb_dict)
        
        threading.Thread(target=send_preview, daemon=True).start()

    except Exception as e:
        print("Error in receive_any_media:", e)
        # Detailed error log for debugging
        import traceback
        traceback.print_exc() 
        send_message(bot_token, msg.get("chat", {}).get("id"), esc("⚠️ Server error, please try again."))

@on_callback_query(filters.callback_data("^rename_file:"))
def rename_file_prompt(bot_token, update, callback_query):
    data = callback_query.get("data", "")
    parts = data.split(":", 1)
    if len(parts) < 2:
        return answer_callback_query(bot_token, callback_query.get("id"), "❌ Invalid callback data.", True)

    file_uuid = parts[1]
    user_id = str(callback_query.get("from", {}).get("id"))

    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        return answer_callback_query(bot_token, callback_query.get("id"), "❌ File not found.", True)

    current_name = file_entry.get("name", "Unnamed")
    file_id = file_entry.get("file_id")
    sub_type = file_entry.get("sub_type", "document")

    # Update status -> file_renaming:<uuid>
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}
    status_data[user_id] = f"file_renaming:{file_uuid}"
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # Delete original message (best-effort)
    msg = callback_query.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    if chat_id and message_id:
        try:
            delete_message(bot_token, chat_id, message_id)
        except Exception:
            pass

    # Send the media back to user with prompt asking for new name
    prompt_caption = (
    f"*{esc('Current File Name:')}*\n"
    f"`{esc(current_name)}`\n\n"
    f"{esc('Please send the')} *{esc('New Name')}* {esc('for this file.')}"
)
    keyboard = None  # no buttons while asking for name

    if sub_type == "document":
        send_document(bot_token, chat_id, document=file_id, caption=prompt_caption)
    elif sub_type == "photo":
        send_photo(bot_token, chat_id, photo=file_id, caption=prompt_caption)
    elif sub_type == "video":
        send_video(bot_token, chat_id, video=file_id, caption=prompt_caption)
    elif sub_type == "audio":
        send_audio(bot_token, chat_id, audio=file_id, caption=prompt_caption)
    else:
        # fallback: just send text prompt
        send_message(bot_token, chat_id, prompt_caption, parse_mode="MarkdownV2")


# -------------------------
# rename_file receive (user sends new name)
# -------------------------
@on_message(filters.private() & filters.text() & StatusFilter("file_renaming:"))
def rename_file_receive(bot_token, update, msg):
    user_id = str(msg.get("from", {}).get("id"))
    new_name = msg.get("text", "").strip()
    chat_id = msg.get("chat", {}).get("id")

    # Load status to get file_uuid
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_val = status_data.get(user_id, "")
    if ":" not in status_val:
        return send_message(bot_token, chat_id, f"{esc('❌ Status error or expired.')}")

    _, file_uuid = status_val.split(":", 1)

    # Load temp file
    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        return send_message(bot_token, chat_id, f"{esc('❌ File not found in your temp data.')}")

    # Update the in-temp name
    file_entry["name"] = new_name

    # Save temp file
    temp_data[user_id]["files"][file_uuid] = file_entry
    with open(temp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    # Clear status
    status_data.pop(user_id, None)
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # Prepare caption and buttons
    file_id = file_entry.get("file_id")
    caption = (
        f"{esc('File Renamed Successfully')}\n\n"
        f"*{esc('New Name')}* : `{esc(new_name)}`\n"
        f"*{esc('Caption')}* : {file_entry.get('caption') or new_name}\n\n"
        f"*{esc('File ID')}* : `{esc(file_id)}`\n"
    )

    visibility = file_entry.get("visibility", "private")
    sub_type = file_entry.get("sub_type", "document")

    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Visibility: {visibility}", callback_data=f"toggle_visibility:{file_uuid}")],
        [InlineKeyboardButton("FILE IS UNDER A USER", callback_data=f"add_premium_owner:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file:{file_uuid}")
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # Send updated media back to user with buttons
    if sub_type == "document":
        send_document(bot_token, chat_id, document=file_id, caption=caption, reply_markup=keyboard)
    elif sub_type == "photo":
        send_photo(bot_token, chat_id, photo=file_id, caption=caption, reply_markup=keyboard)
    elif sub_type == "video":
        send_video(bot_token, chat_id, video=file_id, caption=caption, reply_markup=keyboard)
    elif sub_type == "audio":
        send_audio(bot_token, chat_id, audio=file_id, caption=caption, reply_markup=keyboard)
    else:
        send_message(
        bot_token,
        chat_id,
        f"{esc('❌ Unknown file type.')}",
        reply_markup=keyboard
    )
@on_callback_query(filters.callback_data("^edit_file_caption:"))
def edit_file_caption_prompt(bot_token, update, callback_query):
    """
    callback_query: dict from webhook
    """
    data = callback_query.get("data", "")
    parts = data.split(":", 1)
    if len(parts) < 2:
        return answer_callback_query(
            bot_token,
            callback_query.get("id"),
            f"{esc('❌ Invalid callback data.')}",
            True
        )

    file_uuid = parts[1]
    user_id = str(callback_query.get("from", {}).get("id"))

    # Load temp file
    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        return answer_callback_query(
            bot_token,
            callback_query.get("id"),
            f"{esc('❌ File not found.')}",
            True
        )

    current_caption = file_entry.get("caption", file_entry.get("name", "No caption"))
    file_id = file_entry.get("file_id")
    sub_type = file_entry.get("sub_type", "document")

    # Update status to file_captioning:<uuid>
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = f"file_captioning:{file_uuid}"
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # Acknowledge callback (remove spinner)
    answer_callback_query(bot_token, callback_query.get("id"))

    # Delete original message (best-effort)
    msg = callback_query.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    if chat_id and message_id:
        try:
            delete_message(bot_token, chat_id, message_id)
        except Exception:
            pass

    # Prompt caption (bold * kept outside esc)
    prompt_caption = (
        f"*{esc('Current Caption:')}*\n"
        f"{current_caption}\n\n"
        f"{esc('Now, Please send the')} *{esc('New Caption')}* {esc('for this file.')}"
    )

    # Send media back with caption prompt (non-blocking)
    if sub_type == "document":
        threading.Thread(
            target=send_document,
            args=(bot_token, chat_id, file_id, prompt_caption),
            kwargs={"reply_markup": None},
            daemon=True
        ).start()

    elif sub_type == "photo":
        threading.Thread(
            target=send_photo,
            args=(bot_token, chat_id, file_id, prompt_caption),
            kwargs={"reply_markup": None},
            daemon=True
        ).start()

    elif sub_type == "video":
        threading.Thread(
            target=send_video,
            args=(bot_token, chat_id, file_id, prompt_caption),
            kwargs={"reply_markup": None},
            daemon=True
        ).start()

    elif sub_type == "audio":
        threading.Thread(
            target=send_audio,
            args=(bot_token, chat_id, file_id, prompt_caption),
            kwargs={"reply_markup": None},
            daemon=True
        ).start()

    else:
        send_message(
            bot_token,
            chat_id,
            f"{esc('📝 Please send the new caption for the file.')}"
        )
@on_message(filters.private() & filters.text() & StatusFilter("file_captioning:"))
def edit_caption_receive(bot_token, update, msg):
    user_id = str(msg.get("from", {}).get("id"))
    chat_id = msg.get("chat", {}).get("id")
    raw_text = msg.get("text", "").strip()
    new_caption = get_markdown(msg)

    # Load status to get file_uuid
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_val = status_data.get(user_id, "")
    if ":" not in status_val:
        send_message(bot_token, chat_id, f"{esc('❌ Status error or expired.')}")
        return

    _, file_uuid = status_val.split(":", 1)

    # Load temp data
    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        send_message(bot_token, chat_id, f"{esc('❌ File not found.')}")
        return

    # Update caption
    file_entry["caption"] = new_caption

    # Save tempfile
    temp_data[user_id]["files"][file_uuid] = file_entry
    with open(temp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    # Clear status
    status_data.pop(user_id, None)
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # Prepare response caption and buttons
    file_id = file_entry.get("file_id")
    name = file_entry.get("name")
    visibility = file_entry.get("visibility", "private")
    sub_type = file_entry.get("sub_type", "document")

    caption_text = (
        f"*{esc('Caption Updated Successfully')}*\n\n"
        f"*{esc('Name')}* : `{esc(name)}`\n"
        f"*{esc('New Caption')}* : {new_caption}\n\n"
        f"*{esc('File ID')}* : `{esc(file_id)}`"
    )

    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Visibility: {visibility}", callback_data=f"toggle_visibility:{file_uuid}")],
        [InlineKeyboardButton("FILE IS UNDER A USER", callback_data=f"add_premium_owner:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file:{file_uuid}")
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # Send updated media back to user with buttons (background)
    if sub_type == "document":
        threading.Thread(target=send_document, args=(bot_token, chat_id, file_id, caption_text, keyboard), daemon=True).start()
    elif sub_type == "photo":
        threading.Thread(target=send_photo, args=(bot_token, chat_id, file_id, caption_text, keyboard), daemon=True).start()
    elif sub_type == "video":
        threading.Thread(target=send_video, args=(bot_token, chat_id, file_id, caption_text, keyboard), daemon=True).start()
    elif sub_type == "audio":
        threading.Thread(target=send_audio, args=(bot_token, chat_id, file_id, caption_text, keyboard), daemon=True).start()
    else:
        send_message(bot_token, chat_id, caption_text, reply_markup=keyboard)
        
@on_callback_query(filters.callback_data("^toggle_visibility:"))
def toggle_visibility_callback(bot_token, update, callback_query):

    callback_id = callback_query.get("id")
    user = callback_query.get("from", {})
    user_id = str(user.get("id", ""))
    data = callback_query.get("data", "")
    parts = data.split(":", 1)
    if len(parts) < 2:
        return answer_callback_query(bot_token, callback_id, "❌ Invalid callback data.", True)

    file_uuid = parts[1]

    # load temp file for this bot
    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        return answer_callback_query(bot_token, callback_id, "❌ फ़ाइल नहीं मिली।", True)

    # cycle visibility
    visibility_cycle = ["public", "private", "vip"]
    current_visibility = file_entry.get("visibility", "public")
    try:
        idx = visibility_cycle.index(current_visibility)
    except ValueError:
        idx = 0
    new_visibility = visibility_cycle[(idx + 1) % len(visibility_cycle)]
    file_entry["visibility"] = new_visibility

    # save temp file
    try:
        temp_data[user_id]["files"][file_uuid] = file_entry
        with open(temp_file, "w") as f:
            json.dump(temp_data, f, indent=2)
    except Exception as e:
        # best-effort save error
        print("toggle_visibility save error:", e)
        return answer_callback_query(bot_token, callback_id, "⚠️ Unable to update visibility.", True)
    file_id = file_entry.get("file_id")
    name = file_entry.get("name", "Unnamed")
    caption_text = file_entry.get("caption", name)
    safe_name = str(name)
    safe_caption = caption_text
    caption = (
        f"*{esc('📄 Visibility Updated')}*\n"
        f"*{esc('Name')}* : `{esc(safe_name)}`\n"
        f"*{esc('Caption')}* : {safe_caption}\n\n"
        f"*{esc('File ID')}* : `{esc(file_id)}`\n"
        f"*{esc('Visibility')}* : `{esc(new_visibility)}`"
    )

    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Visibility: {new_visibility}", callback_data=f"toggle_visibility:{file_uuid}")],
        [InlineKeyboardButton("FILE IS UNDER A USER", callback_data=f"add_premium_owner:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file:{file_uuid}")
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # acknowledge callback to remove spinner
    answer_callback_query(bot_token, callback_id)

    # edit original message
    msg = callback_query.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")

    if chat_id and message_id:
        edit_message(bot_token, chat_id, message_id, caption, reply_markup=keyboard, is_caption=True)
    else:
        # fallback: send as new message to user
        send_message(bot_token, user_id, caption, reply_markup=keyboard)

@on_callback_query(filters.callback_data("^add_premium_owner:"))
def cancel_file_handler(bot_token, update, callback_query):
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    return answer_callback_query(bot_token, callback_id, "This Feature Will come Soon...", True)
        
@on_callback_query(filters.callback_data("^cancel_file:"))
def cancel_file_handler(bot_token, update, callback_query):
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    parts = data.split(":", 1)
    if len(parts) < 2:
        return answer_callback_query(bot_token, callback_id, "❌ Invalid callback data.", True)

    file_uuid = parts[1]
    user_id = str(callback_query.get("from", {}).get("id", ""))
    msg = callback_query.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except Exception as e:
        print("cancel_file: failed to load temp file:", e)
        return answer_callback_query(bot_token, callback_id, "❌ tempfile.json not found", True)
    user_files = temp_data.get(user_id, {}).get("files", {})
    if file_uuid in user_files:
        del user_files[file_uuid]
        if not user_files:
            temp_data.pop(user_id, None)
        else:
            temp_data[user_id]["files"] = user_files
        try:
            with open(temp_file, "w") as f:
                json.dump(temp_data, f, indent=2)
        except Exception as e:
            print("cancel_file: failed to save temp file:", e)
            return answer_callback_query(bot_token, callback_id, "⚠️ Unable to update temp storage.", True)
        answer_callback_query(bot_token, callback_id)
        if chat_id and message_id:
            try:
                edit_message(
        bot_token,
        chat_id,
        message_id,
        f"{esc('❌ File upload cancelled successfully.')}",
        reply_markup=None,
        is_caption=True
)
            except Exception as e:
                print("cancel_file: edit_message failed:", e)
                send_message(bot_token, chat_id, f"{esc('❌ File upload cancelled successfully.')}")
        else:
            send_message(bot_token, user_id, f"{esc('❌ File upload cancelled successfully.')}")
    else:
        return answer_callback_query(bot_token, callback_id, "❌ File not found or already cancelled.", True)

def find_folder_id_of_item(folder, target_id):
    for item in folder.get("items", []):
        if item.get("id") == target_id:
            return folder.get("id")
        elif item.get("type") == "folder":
            found = find_folder_id_of_item(item, target_id)
            if found:
                return found
    return None
def find_item_by_id(folder, target_id):
    for item in folder.get("items", []):
        if item["id"] == target_id:
            return item
        if item.get("type") == "folder":
            found = find_item_by_id(item, target_id)
            if found:
                return found
    return None        
@on_callback_query(filters.callback_data("^confirm_file:"))
def confirm_file_callback(bot_token, update, callback_query):
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    parts = data.split(":", 1)
    bot_id = bot_token.split(":")[0]
    if len(parts) < 2:
        print("INVALID")
        return answer_callback_query(bot_token, callback_id, "❌ Invalid callback data.", True)
    file_uuid = parts[1] 
    user = callback_query.get("from", {})
    user_id = str(user.get("id", ""))

    # acknowledge callback quickly
    answer_callback_query(bot_token, callback_id)
    temp_file = get_temp_file(bot_token)
    try:
        with open(temp_file, "r") as f:
            temp_data = json.load(f)
    except Exception as e:
        return answer_callback_query(bot_token, callback_id, "❌ Temp file data not found.", True)
    user_files = temp_data.get(user_id, {}).get("files", {})
    file_data = user_files.get(file_uuid)
    if not file_data:
        #print("File not found in tem")
        return answer_callback_query(bot_token, callback_id, "❌ File not found in temp.", True)
    folder_id = temp_data.get(user_id, {}).get("folder_id")
    if not folder_id:
        return answer_callback_query(bot_token, callback_id, "❌ Folder info missing.", True)
    if (not is_user_action_allowed(folder_id, "add_file", bot_token)
            and int(user_id) not in ADMINS(bot_id)
            and get_created_by_from_folder(bot_token, folder_id) != int(user_id)):
        return answer_callback_query(bot_token, callback_id, "❌ You are not allowed to add a file in this folder.", True)
    data_file = get_data_file(bot_token)
    try:
        with open(data_file, "r") as f:
            bot_data = json.load(f)
    except Exception as e:
        print("confirm_file: could not open data file:", e)
        return answer_callback_query(bot_token, callback_id, "❌ bot_data.json not found.", True)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)
    if not parent:
        return answer_callback_query(bot_token, callback_id, "❌ Parent folder not found.", True)

    # compute next row
    existing_rows = [item.get("row", 0) for item in parent.get("items", [])]
    next_row = max(existing_rows, default=-1) + 1

    # determine created_by (premium owner override)
    if file_data.get("premium_owner"):
        try:
            created_by_val = int(file_data["premium_owner"])
        except Exception:
            created_by_val = int(user_id)
    else:
        created_by_val = int(user_id)

    # prepare final item
    final_file = {
        "id": file_data["id"],
        "type": "file",
        "sub_type": file_data.get("sub_type", "document"),
        "name": file_data.get("name"),
        "file_id": file_data.get("file_id"),
        "caption": file_data.get("caption"),
        "visibility": file_data.get("visibility", "private"),
        "row": next_row,
        "column": 0,
        "created_by": created_by_val,
    }
    if file_data.get("premium_owner"):
        try:
            final_file["premium_owner"] = int(file_data["premium_owner"])
        except Exception:
            pass
    parent.setdefault("items", []).append(final_file)
    try:
        with open(data_file, "w") as f:
            json.dump(bot_data, f, indent=2)
    except Exception as e:
        print("confirm_file: failed to save data file:", e)
        return answer_callback_query(bot_token, callback_id, "⚠️ Failed to save bot data.", True)
    try:
        pre_file_path = get_pre_files_file(bot_token)
    except Exception:
        pre_file_path = None
    if file_data.get("premium_owner") and pre_file_path:
        try:
            try:
                with open(pre_file_path, "r") as f:
                    pre_files_data = json.load(f)
            except FileNotFoundError:
                pre_files_data = {}
            owner_key = str(file_data.get("premium_owner"))
            pre_files_data.setdefault(owner_key, [])
            if file_uuid not in pre_files_data[owner_key]:
                pre_files_data[owner_key].append(file_uuid)
            with open(pre_file_path, "w") as f:
                json.dump(pre_files_data, f, indent=2)
        except Exception as e:
            print("confirm_file: failed to update pre_files:", e)
    try:
        user_entry = temp_data.get(user_id, {})
        user_files_map = user_entry.get("files", {})
        if file_uuid in user_files_map:
            del user_files_map[file_uuid]
        # if no files left, remove user entry
        if not user_files_map:
            temp_data.pop(user_id, None)
        else:
            temp_data[user_id]["files"] = user_files_map
        with open(temp_file, "w") as f:
            json.dump(temp_data, f, indent=2)
    except Exception as e:
        print("confirm_file: failed to cleanup temp_data:", e)
    status_file = get_status_file(bot_token)
    try:
        with open(status_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}
    status_data.pop(user_id, None)
    with open(status_file, "w") as f:
        json.dump(status_data, f, indent=2)
    git_data_file= f"BOT_DATA/{bot_id}/bot_data.json"
    save_json_to_alt_github(data_file,git_data_file)

    # refresh UI: edit caption to wait then success
    msg = callback_query.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    kb = generate_folder_keyboard(parent, int(user_id),bot_id)
    success_caption = (
    f"{esc('FILE SAVED SUCCESSFULLY')}\n"
    f"*{esc('File uuid')}*: `{esc(file_data.get('id'))}`"
)
    if chat_id and message_id:
        edit_message(bot_token, chat_id, message_id, success_caption, reply_markup=kb, is_caption=True)
    else:
        # fallback: send message to user
        send_message(bot_token, user_id, success_caption, reply_markup=kb)
        
@on_callback_query(filters.callback_data("^file:"))
def send_file_from_json(bot_token, update, callback_query):
    try:
        callback_id = callback_query.get("id")
        data = callback_query.get("data", "") or ""
        data_parts = data.split(":")
        bot_id = bot_token.split(":")[0]
        if len(data_parts) < 2:
            return answer_callback_query(bot_token, callback_id, "❌ Invalid callback.", True)

        file_uuid = data_parts[1]
        user = callback_query.get("from", {}) or {}
        user_id = int(user.get("id", 0))
        msg = callback_query.get("message", {}) or {}
        chat = msg.get("chat", {}) or {}
        chat_id = chat.get("id")
        chat_type = chat.get("type", "")

        # helper: detect group
        is_group = chat_type in ("group", "supergroup")

        # If group - enforce original user check and redirect to @bot?start=
        if is_group:
            if len(data_parts) < 3:
                return answer_callback_query(bot_token, callback_id, "❌ Invalid file request.", True)
            try:
                original_user_id = int(data_parts[2])
            except Exception:
                return answer_callback_query(bot_token, callback_id, "❌ Invalid original user id.", True)

            if original_user_id != user_id:
                return answer_callback_query(
                    bot_token,
                    callback_id,
                    "⚠️ This button belongs to another user.\nPlease send /start to get your own menu.",
                    True
                )

            # get bot username via getMe
            me_resp = send_api(bot_token, "getMe", {})
            bot_username = None
            if me_resp and me_resp.get("ok"):
                bot_username = me_resp.get("result", {}).get("username")
            if bot_username:
                start_url = f"https://t.me/{bot_username}?start={file_uuid}"
                # answer with url (opens private chat)
                return answer_callback_query(bot_token, callback_id, None) or send_message(bot_token, chat_id, f"{esc('Open in private:')} {esc(start_url)}")
            else:
                return answer_callback_query(bot_token, callback_id, "❌ Unable to get bot username.", True)
        data_file = get_data_file(bot_token)
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                bot_data = json.load(f)
        except Exception as e:
            print("send_file_from_json: failed to load data_file:", e)
            return answer_callback_query(bot_token, callback_id, f"❌ Data file not found: {e}", True)

        root = bot_data.get("data", {})
        file_data = find_item_by_id(root, file_uuid)  # must return the item dict or None

        if not file_data or file_data.get("type") != "file":
            return answer_callback_query(bot_token, callback_id, "❌ File not found.", True)

        file_id = file_data.get("file_id")
        name = file_data.get("name", "Unnamed")
        caption = file_data.get("caption") or name
        sub_type = file_data.get("sub_type", "document")
        visibility = file_data.get("visibility", "public")
        created_by = file_data.get("created_by")
        protect = visibility == "private"
        premium_owner = file_data.get("premium_owner")  # may be None or int
        owner_id = int(get_owner_id(bot_token))
        deploy = BASE_URL.rstrip("/") if globals().get("BASE_URL") else ""
        unlock_base_url = deploy + f"/{bot_id}/unlock_file"
        def send_media_api(bot_token_, chat_id_, sub_type_, file_id_, caption_, reply_markup=None, protect_content=False):
            method = {
                "photo": "sendPhoto",
                "video": "sendVideo",
                "audio": "sendAudio",
                "document": "sendDocument",
            }.get(sub_type_, "sendDocument")
            payload = {"chat_id": chat_id_, "parse_mode": "MarkdownV2"}
            if method == "sendPhoto":
                payload["photo"] = file_id_
            elif method == "sendVideo":
                payload["video"] = file_id_
            elif method == "sendAudio":
                payload["audio"] = file_id_
            else:
                payload["document"] = file_id_
            if caption_ is not None:
                payload["caption"] = caption_
            if protect_content:
                payload["protect_content"] = True
            if reply_markup:
                if hasattr(reply_markup, "to_dict"):
                    payload["reply_markup"] = reply_markup.to_dict()
                elif isinstance(reply_markup, dict):
                    payload["reply_markup"] = reply_markup
            return send_api(bot_token_, method, payload)

        # ----------------------
        # VIP handling
        # ----------------------
        if visibility == "vip":
            try:
                # Send a copy to PREMIUM_CHECK_LOG to get file_size etc.
                #premium_chat = PREMIUM_CHECK_LOG
              if get_is_monetized(bot_id):
                premium_chat = get_file_channel_id(bot_token)
                resp = send_media_api(bot_token, premium_chat, sub_type, file_id, caption, reply_markup=None, protect_content=False)
                # extract file size
                file_size = None
                if resp and resp.get("ok"):
                    result = resp.get("result", {})
                    if sub_type == "document" and result.get("document"):
                        file_size = result["document"].get("file_size")
                    elif sub_type == "video" and result.get("video"):
                        file_size = result["video"].get("file_size")
                    elif sub_type == "audio" and result.get("audio"):
                        file_size = result["audio"].get("file_size")
                    elif sub_type == "photo" and result.get("photo"):
                        # photo is list
                        photos = result.get("photo", [])
                        if photos:
                            file_size = photos[-1].get("file_size")
                readable_size = f"{round(file_size / (1024 * 1024), 2)} MB" if file_size else "Unknown"

                import urllib.parse
                base_unlock = "https://reward.edumate.life/Premium/unlock.html?"
                # if premium_owner, use different unlock endpoint
                if premium_owner:
                    unlock_base_url = deploy + f"/{bot_id}/unlock_users_file"

                unlock_params = (
                    f"uuid={urllib.parse.quote_plus(file_uuid)}"
                    f"&file_name={urllib.parse.quote_plus(name)}"
                    f"&file_des={urllib.parse.quote_plus(str(caption))}"
                    f"&file_size={urllib.parse.quote_plus(readable_size)}"
                    f"&url={urllib.parse.quote_plus(unlock_base_url)}"
                )
                unlock_url = base_unlock + unlock_params
                # Build unlock message
                if premium_owner and int(user_id) == int(premium_owner):
                    unlock_msg = (
                        f"*{esc('Hello Partner')}*,\n"
                        f"{esc('You are Making Money by this file.')}\n\n"
                        f"*{esc('📁 Name:')}* `{esc(str(name))}`  \n"
                        f"*{esc('📝 Description:')}* `{esc(str(caption))}`  \n"
                        f"*{esc('📦 Size:')}* `{esc(readable_size)}`  \n"
                        f"*{esc('🆔 File UUID:')}* `{esc(file_uuid)}`\n\n"
                        f"{esc('Manage this file with command')} `/my_pdf {esc(file_uuid)}`"
                    )
                else:
                    unlock_msg = (
                        f"*{esc('🔐 Exclusive Premium File')}*\n\n"
                        f"*{esc('📁 Name:')}* `{esc(str(name))}`  \n"
                        f"*{esc('📝 Description:')}* `{esc(str(caption))}`  \n"
                        f"*{esc('📦 Size:')}* `{esc(readable_size)}`\n\n"
                        f"{esc('To unlock this file, tap')} *{esc('Unlock Now')}* {esc('below and view a short ad. 🙏')}\n👇"
                    )

                # build buttons (web_app)
                buttons = [[InlineKeyboardButton("🔓 Unlock this file", web_app={"url": unlock_url})]]

                # add admin/edit button if allowed
                try:
                    allowed_user = (user_id in ADMINS(bot_id)) or (user_id == created_by) or (premium_owner and int(user_id) == int(premium_owner))
                except Exception:
                    allowed_user = (user_id == created_by) or (premium_owner and int(user_id) == int(premium_owner))
                if allowed_user:
                    folder_of_item = find_folder_id_of_item(root, file_uuid)
                    if folder_of_item:
                        buttons.append([InlineKeyboardButton("✏️ Edit Item", callback_data=f"edit_item_file:{folder_of_item}:{file_uuid}")])

                kb = InlineKeyboardMarkup(buttons)
                # reply with unlock message
                send_media_api(bot_token, chat_id, sub_type, file_id, unlock_msg, reply_markup=kb, protect_content=False)
                answer_callback_query(bot_token, callback_id)
                return
              else: 
                premium_chat = get_file_channel_id(bot_token)
                resp = send_media_api(
                bot_token,
                owner_id,
                sub_type,
                file_id,
                f"{esc('Someone accessed your VIP file.')}\n\n"
                f"{esc('But your bot is not monetized yet.')}\n"
                f"{esc('Please monetize your bot to enable ads and earn money.')}\n\n"
                f"{esc('To monetize your bot visit bot @BotixHubBot')}",
                reply_markup=None,
                protect_content=False
)
                resp = send_media_api(
                bot_token,
                premium_chat,
                sub_type,
                file_id,
                f"{esc('This file is a VIP file. But your bot is not monetized yet.')}\n"
                f"{esc('Please monetize your bot to enable ads and earn money.')}\n\n"
                f"{esc('To monetize your bot visit bot @BotixHubBot')}",
                reply_markup=None,
                protect_content=False
)
                
            except Exception as e:
                print("send_file_from_json VIP error:", e)
                answer_callback_query(bot_token, callback_id)
                send_message(bot_token, chat_id, f"❌ Failed to prepare VIP file: {e}")
                return
        buttons = []
        try:
            allowed_user = (user_id in ADMINS(bot_id)) or (user_id == created_by) or (premium_owner and int(user_id) == int(premium_owner))
        except Exception:
            allowed_user = (user_id == created_by) or (premium_owner and int(user_id) == int(premium_owner))

        if allowed_user:
            folder_of_item = find_folder_id_of_item(root, file_uuid)
            if folder_of_item:
                buttons.append([InlineKeyboardButton("✏️ Edit Item", callback_data=f"edit_item_file:{folder_of_item}:{file_uuid}")])

        kb = InlineKeyboardMarkup(buttons) if buttons else None

        # send file to same chat (chat_id)
        try:
            send_resp = send_media_api(bot_token, chat_id, sub_type, file_id, caption, reply_markup=kb, protect_content=protect)
            # ignore send_resp details; it's fine
            answer_callback_query(bot_token, callback_id)
            return
        except Exception as e:
            print("send_file_from_json send error:", e)
            answer_callback_query(bot_token, callback_id)
            send_message(bot_token, chat_id, f"❌ Error sending file: {e}")
            return

    except Exception as e:
        print("⚠️ send_file_from_json callback error:", e)
        try:
            answer_callback_query(bot_token, callback_query.get("id"), f"❌ Unexpected error: {e}", True)
        except Exception:
            pass
          
@on_callback_query(filters.callback_data("^edit_item_file:"))
def edit_item_file_handler(bot_token, update, callback_query):
    callback_id = callback_query.get("id")
    #print(callback_query)
    data = callback_query.get("data", "") or ""
    parts = data.split(":")
    bot_id = bot_token.split(":")[0]
    if len(parts) < 3:
        return answer_callback_query(bot_token, callback_id, "❌ Invalid callback data.", True)

    folder_id = parts[1]
    file_uuid = parts[2]

    user = callback_query.get("from", {}) or {}
    user_id = int(user.get("id", 0))

    # load bot_data (bot-specific)
    data_file = get_data_file(bot_token)
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data_json = json.load(f)
    except Exception as e:
        print("edit_item_file: failed to open data file:", e)
        return answer_callback_query(bot_token, callback_id, "❌ Unable to load data.", True)

    # recursive folder finder
    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []) or []:
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    root = data_json.get("data", {})
    folder = find_folder(root, folder_id)
    if not folder:
        return answer_callback_query(bot_token, callback_id, "❌ Folder not found.", True)

    # find file item inside folder
    file_data = next((i for i in folder.get("items", []) if i.get("id") == file_uuid), None)
    #print(f"F8ledgyd: {file_data}")
    if not file_data:
        return answer_callback_query(bot_token, callback_id, "❌ File not found.", True)

    # permission check: admins or creator
    try:
        admins = ADMINS(bot_id)
    except Exception:
        admins = ADMINS(bot_id) if callable(ADMINS) else []
    if (user_id not in admins) and (file_data.get("created_by") != user_id):
        return answer_callback_query(bot_token, callback_id, "❌ You don't have access.", True)

    # get current visibility
    visibility = file_data.get("visibility", "private")

    # build buttons
    buttons = [
        [InlineKeyboardButton(f"👁 Visibility: {visibility}", callback_data=f"toggle_file_visibility:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"file_caption_editing:{file_uuid}")],
    ]
    kb = InlineKeyboardMarkup(buttons)

    # edit the message text (use edit_message_text helper)
    msg = callback_query.get("message", {}) or {}
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    text = f"{esc('🛠 Edit options for file:')} {esc(file_data.get('name', 'Unnamed'))}"
    answer_callback_query(bot_token, callback_id)
    if chat_id and message_id:
        a= edit_message(bot_token, chat_id, message_id, text, reply_markup=kb, is_caption=True)
        print("edit")
        print(a)
    else:
        a= send_message(bot_token, user_id, text, reply_markup=kb)
        print("here")
        print(a)

@on_callback_query()
def edit_item_file_handler(bot_token, update, callback_query):
  callback_id = callback_query.get("id")
  return answer_callback_query(bot_token, callback_id, "This Feature is Comming Soon...", True)
