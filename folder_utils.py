# folder_utils.py
import json
from collections import defaultdict
from pathlib import Path
from common_data import BASE_PATH
BASE_PATH = Path(BASE_PATH)
from keyboard_utils import ADMINS  # uses BASE_PATH from keyboard_utils
from script import get_bot_folder
from framework import esc
def load_bot_data(bot_token: str):
    bot_id = bot_token.split(":")[0]
    data_file = BASE_PATH / "BOT_DATA" / bot_id / "bot_data.json"
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def find_folder_by_id(folder: dict, folder_id: str):
    if not isinstance(folder, dict):
        return None
    if folder.get("id") == folder_id:
        return folder
    for item in folder.get("items", []) or []:
        if item.get("type") == "folder":
            found = find_folder_by_id(item, folder_id)
            if found:
                return found
    return None
def get_data_file(bot_token: str) -> str:
    return os.path.join(get_bot_folder(bot_token), "bot_data.json")
    

def generate_folder_keyboard(folder: dict, user_id: int, bot_id: str):
    layout = defaultdict(dict)
    folder_id = folder.get("id", "unknown")

    for item in folder.get("items", []) or []:
        row = item.get("row", 0)
        col = item.get("column", 0)
        typ = item.get("type", "")
        name = item.get("name", "Item")
        button = None
        if typ == "folder":
            button = {"text": name, "callback_data": f"open:{item.get('id')}"}
        elif typ == "file":
            button = {"text": name, "callback_data": f"file:{item.get('id')}"}
        elif typ == "url":
            button = {"text": name, "url": item.get("url", "#")}
        elif typ == "webapp":
            button = {"text": name, "web_app": {"url": item.get("url", "#")}}
        if button:
            layout[row][col] = button

    rows = []
    for row in sorted(layout.keys()):
        cols = layout[row]
        rows.append([cols[col] for col in sorted(cols.keys())])

    # Admin / creator controls
    try:
        created_by = int(folder.get("created_by")) if folder.get("created_by") is not None else None
    except Exception:
        created_by = None

    if user_id in ADMINS(bot_id) or created_by == user_id:
        rows.append([
            {"text": "➕ Add File", "callback_data": f"add_file:{folder_id}"},
            {"text": "📁 Add Folder", "callback_data": f"add_folder:{folder_id}"}
        ])
        rows.append([
            {"text": "🧩 Add WebApp", "callback_data": f"add_webapp:{folder_id}"},
            {"text": "🔗 Add URL", "callback_data": f"add_url:{folder_id}"}
        ])
        rows.append([{"text": "✏️ Edit Folder Layout", "callback_data": f"edit1_item1:{folder_id}"}])
    else:
        allow = folder.get("user_allow", []) or []
        user_buttons = []
        if "add_file" in allow:
            user_buttons.append({"text": "➕ Add File", "callback_data": f"add_file:{folder_id}"})
        if "add_folder" in allow:
            user_buttons.append({"text": "📁 Add Folder", "callback_data": f"add_folder:{folder_id}"})
        if "add_webapp" in allow:
            user_buttons.append({"text": "🧩 Add WebApp", "callback_data": f"add_webapp:{folder_id}"})
        if "add_url" in allow:
            user_buttons.append({"text": "🔗 Add URL", "callback_data": f"add_url:{folder_id}"})
        for i in range(0, len(user_buttons), 2):
            rows.append(user_buttons[i:i+2])

    # Back button
    parent_id = folder.get("parent_id")
    if parent_id:
        rows.append([{"text": "🔙Back", "callback_data": f"open:{parent_id}"}])

    return {"inline_keyboard": rows}

# सुनिश्चित करें कि esc फंक्शन यहाँ उपलब्ध है (या import किया गया है)
# from framework import esc 

def process_open_callback(bot_token: str, callback_data: str, user_info: dict, chat_id: int):
    """
    Returns (text, keyboard_dict)
    """
    bot_id = bot_token.split(":")[0]
    full_data = load_bot_data(bot_token)
    if not full_data:
        return esc("❌ Bot data not found."), None

    root = full_data.get("data", {})
    folder_id = callback_data.split(":", 1)[1]
    folder = find_folder_by_id(root, folder_id)
    if not folder:
        return esc("❌ Folder not found."), None

    # 1. User Info निकालें और उन्हें ESCAPE करें
    # (क्योंकि हम इन्हें MarkdownV2 स्ट्रिंग के अंदर डालने वाले हैं)
    
    raw_first = user_info.get("first_name", "") or ""
    raw_last = user_info.get("last_name", "") or ""
    raw_username = user_info.get("username", "") or ""
    uid = str(user_info.get("id", ""))

    # वेरिएबल्स को सुरक्षित बनाएं (ताकि नाम में dot/dash होने पर एरर न आए)
    first = esc(raw_first)
    last = esc(raw_last)
    full = esc((raw_first + " " + raw_last).strip())
    username = esc(raw_username)

    # Mention सिंटैक्स: [Name](tg://user?id=123)
    # Name पहले ही esc हो चुका है, जो सही है।
    mention = f"[{first}](tg://user?id={uid})" if first else f"[{esc('User')}](tg://user?id={uid})"

    # 2. डिस्क्रिप्शन लोड करें
    # हम मान कर चल रहे हैं कि 'saved description' पहले से get_markdown() से पास होकर आया है (Formatted है)।
    # लेकिन अगर description खाली है, तो Default Text को esc() करना जरूरी है।
    
    raw_text = folder.get("description")
    
    if not raw_text:
        # अगर डिस्क्रिप्शन नहीं है, तो डिफ़ॉल्ट टेक्स्ट को एस्केप करके सेट करें
        raw_text = esc("Hello 👋 Select an option below:")

    # 3. प्लेसहोल्डर्स बदलें (Replace)
    # अब safe variables का use करें
    text = raw_text.replace("${first_name}", first) \
        .replace("${last_name}", last) \
        .replace("${full_name}", full) \
        .replace("${id}", uid) \
        .replace("${username}", username) \
        .replace("${mention}", mention) \
        .replace("${link}", f"tg://user?id={uid}")

    # 4. कीबोर्ड जनरेट करें
    keyboard = generate_folder_keyboard(folder, int(user_info.get("id", 0)), bot_id)
    
    # .to_dict() यहाँ नहीं, बल्कि edit_message_text में कॉल होता है, 
    # लेकिन अगर generate_folder_keyboard dict नहीं लौटा रहा तो चेक कर लें।
    return text, keyboard
