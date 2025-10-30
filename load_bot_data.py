import os
import json
import requests
import logging
from common_data import BASE_PATH, BOTS_JSON_PATH, ALT_GITHUB_TOKEN, ALT_REPO
# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

GITHUB_TOKEN = ALT_GITHUB_TOKEN
GITHUB_REPO = ALT_REPO
if not GITHUB_TOKEN:
    logging.error("❌ GitHub Token नहीं मिला! कृपया GITHUB_TOKEN env में सेट करें।")
    exit(1)

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# ---------- Recursive Downloader ----------
def download_folder_from_github(api_url, local_folder):
    """Recursively download a folder from GitHub"""
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            logging.error(f"❌ {api_url} एक्सेस नहीं हो सका ({response.status_code})")
            return

        items = response.json()
        if isinstance(items, dict) and items.get("message"):
            logging.error(f"GitHub Error: {items.get('message')}")
            return

        for item in items:
            name = item["name"]
            local_path = os.path.join(local_folder, name)

            if item["type"] == "dir":
                os.makedirs(local_path, exist_ok=True)
                download_folder_from_github(item["url"], local_path)

            elif item["type"] == "file":
                try:
                    file_data = requests.get(item["download_url"], headers=HEADERS, timeout=20)
                    if file_data.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(file_data.content)
                        logging.info(f"✅ Downloaded: {local_path}")
                    else:
                        logging.warning(f"⚠️ File download failed: {name} ({file_data.status_code})")
                except Exception as e:
                    logging.error(f"❌ File download error for {name}: {e}")

    except Exception as e:
        logging.error(f"❌ Recursive error at {api_url}: {e}")

def download_all_bot_data():
    if not os.path.exists(BOTS_JSON_PATH):
        logging.error(f"❌ bots.json फ़ाइल नहीं मिली: {BOTS_JSON_PATH}")
        return

    try:
        with open(BOTS_JSON_PATH, "r", encoding="utf-8") as f:
            bots_data = json.load(f)
    except Exception as e:
        logging.error(f"❌ bots.json पढ़ने में त्रुटि: {e}")
        return

    for bot_id, info in bots_data.items():
        github_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/BOT_DATA/{bot_id}"
        local_dir = os.path.join(BASE_PATH, "BOT_DATA", str(bot_id))
        os.makedirs(local_dir, exist_ok=True)

        logging.info(f"🚀 Downloading data for bot_id={bot_id} ({info.get('username', 'Unknown')}) ...")
        download_folder_from_github(github_api_url, local_dir)
        logging.info(f"✅ Completed download for bot_id={bot_id}\n")

    