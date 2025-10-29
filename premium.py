import os
import json, pytz
from common_data import BASE_PATH
from datetime import datetime, timedelta



def has_active_premium(bot_id):
    """
    Check if the bot has an active premium subscription (based on Indian Time).
    Returns True if premium is active, otherwise False.
    """

    # फाइल पथ
    premium_file = os.path.join(BASE_PATH, "BOT_DATA", bot_id, "premium.json")

    # अगर फाइल नहीं मिली तो False
    if not os.path.exists(premium_file):
        return False

    # JSON पढ़ो
    try:
        with open(premium_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading premium.json: {e}")
        return False

    # Indian Time Zone
    india_tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india_tz)

    # सभी entries check करो
    for entry in data:
        try:
            start = india_tz.localize(datetime.strptime(entry["start_date_and_time"], "%Y-%m-%d %H:%M:%S"))
            expire = india_tz.localize(datetime.strptime(entry["expire_date_and_time"], "%Y-%m-%d %H:%M:%S"))

            if start <= now <= expire:
                return True
        except Exception as e:
            print(f"⚠️ Error in entry parsing: {e}")
            continue

    # अगर कोई भी active नहीं मिला
    return False
    
import os, json, pytz, uuid
from datetime import datetime, timedelta

def save_a_premium(price, days, bot_id, plan_id=None):
    """
    Save a new premium plan for the bot.
    Avoid duplicate saves using plan_id.
    Automatically starts after current active premium (if any).
    """

    # ✅ File path
    premium_file = os.path.join(BASE_PATH, "BOT_DATA", bot_id, "premium.json")
    os.makedirs(os.path.dirname(premium_file), exist_ok=True)

    # ✅ Load existing premium data
    try:
        with open(premium_file, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    # ✅ If no plan_id provided, generate new one
    if plan_id is None:
        plan_id = str(uuid.uuid4())

    # ⚠️ Check for duplicate plan_id
    for entry in data:
        if entry.get("plan_id") == plan_id:
            print(f"⚠️ Duplicate plan detected for bot {bot_id}, skipping save.")
            return entry  # Return existing entry

    # 🕒 Timezone setup
    india_tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india_tz)

    # 🔍 Get last active premium (if exists)
    active_premium = None
    for entry in data:
        expire = india_tz.localize(datetime.strptime(entry["expire_date_and_time"], "%Y-%m-%d %H:%M:%S"))
        if expire > now:
            active_premium = entry

    # 📅 Determine start and expire times
    if active_premium:
        start = india_tz.localize(datetime.strptime(active_premium["expire_date_and_time"], "%Y-%m-%d %H:%M:%S"))
    else:
        start = now

    expire = start + timedelta(days=days)

    # 🆕 Prepare new entry
    new_entry = {
        "plan_id": plan_id,
        "price": str(price),
        "days": days,
        "purchase_date_and_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "start_date_and_time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "expire_date_and_time": expire.strftime("%Y-%m-%d %H:%M:%S")
    }

    # ➕ Add and Save
    data.append(new_entry)
    with open(premium_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Premium plan saved for bot {bot_id} (Plan ID: {plan_id})")
    return new_entry

def get_premium_status(bot_id):
    """
    Returns current active premium plan and upcoming plans (based on Indian time).
    {
        "active": {...} or None,
        "upcoming": [{...}, {...}]
    }
    """

    premium_file = os.path.join(BASE_PATH, "BOT_DATA", bot_id, "premium.json")
    if not os.path.exists(premium_file):
        return {"active": None, "upcoming": []}

    try:
        with open(premium_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading premium.json: {e}")
        return {"active": None, "upcoming": []}

    india_tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india_tz)

    active_plan = None
    upcoming_plans = []

    for entry in data:
        try:
            start = india_tz.localize(datetime.strptime(entry["start_date_and_time"], "%Y-%m-%d %H:%M:%S"))
            expire = india_tz.localize(datetime.strptime(entry["expire_date_and_time"], "%Y-%m-%d %H:%M:%S"))

            # ✅ अगर current time start और expire के बीच है
            if start <= now <= expire:
                active_plan = entry

            # 🕒 अगर future में start होगा
            elif start > now:
                upcoming_plans.append(entry)

        except Exception as e:
            print(f"⚠️ Error parsing entry: {e}")
            continue

    return {"active": active_plan, "upcoming": upcoming_plans}