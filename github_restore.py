import os
import requests
import logging
from common_data import BASE_PATH, ALT_GITHUB_TOKEN, ALT_REPO

# Setup Logging
logging.basicConfig(level=logging.INFO)

GITHUB_TOKEN = ALT_GITHUB_TOKEN
GITHUB_REPO = ALT_REPO
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def download_folder_from_github(api_url, local_folder):
    """
    Recursively download a folder from GitHub
    """
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=20)
        
        # 404 means folder doesn't exist on GitHub
        if response.status_code == 404:
            logging.warning(f"⚠️ Folder not found on GitHub: {api_url}")
            return False
            
        if response.status_code != 200:
            logging.error(f"❌ GitHub Error ({response.status_code}): {api_url}")
            return False

        items = response.json()
        if isinstance(items, dict) and items.get("message"):
            logging.error(f"GitHub Message: {items.get('message')}")
            return False

        # Ensure local folder exists
        os.makedirs(local_folder, exist_ok=True)

        for item in items:
            name = item["name"]
            local_path = os.path.join(local_folder, name)

            if item["type"] == "dir":
                # Recursive Call for sub-folders
                download_folder_from_github(item["url"], local_path)

            elif item["type"] == "file":
                try:
                    file_data = requests.get(item["download_url"], headers=HEADERS, timeout=20)
                    if file_data.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(file_data.content)
                    else:
                        logging.warning(f"⚠️ File download failed: {name}")
                except Exception as e:
                    logging.error(f"❌ File write error: {e}")
        return True

    except Exception as e:
        logging.error(f"❌ Network error: {e}")
        return False

def restore_specific_bot_data(bot_id):
    """
    Sirf specific bot_id ka data GitHub se download karta hai
    """
    # 1. API URL Construct karein
    github_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/BOT_DATA/{bot_id}"
    
    # 2. Local Path define karein
    local_dir = os.path.join(BASE_PATH, "BOT_DATA", str(bot_id))
    
    # 3. Download shuru karein
    return download_folder_from_github(github_api_url, local_dir)
