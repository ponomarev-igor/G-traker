import json
import os
import base64
from datetime import date
import requests

today = date.today()
today_str = today.isoformat()

try:
    oauth2 = json.loads(base64.b64decode(os.environ["GARMIN_OAUTH2"]).decode("utf-8"))
    access_token = oauth2["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0",
        "nk": "NT"
    }

    base = "https://connectapi.garmin.com"

    # Профиль
    profile = requests.get(f"{base}/userprofile-service/userprofile/personal-information", headers=headers).json()
    print(f"Profile response: {list(profile.keys()) if isinstance(profile, dict) else profile}")
    display_name = profile.get("displayName") or profile.get("userName", "")
    print(f"✅ display_name: {display_name}")

    # Шаги
    steps = 0
    try:
        steps_data = requests.get(f"{base}/wellness-service/wellness/dailySummaryChart/{display_name}?date={today_str}", headers=headers).json()
        if isinstance(steps_data, list):
            steps = sum(e.get("steps", 0) for e in steps_data)
    except: pass

    # Статистика
    calories, resting_hr, stress = 0, 0, 0
    try:
        stats = requests.get(f"{base}/usersummary-service/usersummary/daily/{display_name}?calendarDate={today_str}", headers=headers).json()
        calories   = int(stats.get("totalKilocalories", 0))
        resting_hr = stats.get("restingHeartRate", 0)
        stress     = stats.get("averageStressLevel", 0)
    except: pass

    # Сон
    sleep_hours = 0
    try:
        sleep_data = requests.get(f"{base}/wellness-service/wellness/dailySleepData/{display_name}?date={today_str}&nonSleepBufferMinutes=60", headers=headers).json()
        if sleep_data and "dailySleepDTO" in sleep_data:
            sleep_hours = round(sleep_data["dailySleepDTO"].get("sleepTimeSeconds", 0) / 3600, 1)
    except: pass

    # Body Battery
    battery = 0
    try:
        bb = requests.get(f"{base}/wellness-service/wellness/bodyBattery/reading/day/{today_str}", headers=headers).json()
        if isinstance(bb, list) and bb:
            last = bb[-1]
            battery = last[1] if isinstance(last, list) else last.get("bodyBatteryLevel", 0)
    except: pass

    result = {
        "date": today_str,
        "steps": steps,
        "sleep_hours": sleep_hours,
        "calories": calories,
        "resting_hr": resting_hr,
        "stress": stress,
        "body_battery": battery,
    }
    print(f"✅ Данные: {result}")

except Exception as e:
    print(f"⚠️ Ошибка: {e}")
    result = {
        "date": today_str,
        "steps": 0, "sleep_hours": 0, "calories": 0,
        "resting_hr": 0, "stress": 0, "body_battery": 0,
        "error": str(e)
    }

with open("garmin.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("✅ garmin.json сохранён")
