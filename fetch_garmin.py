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
        "User-Agent": "GCM-iOS-5.7.2.1 (com.garmin.connect.mobile; build:5.7.2.1; iOS 16.4.0) Alamofire/5.6.4",
        "nk": "NT",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "di-backend": "connectapi.garmin.com",
        "x-app-ver": "5.7.2.1",
        "x-lang": "en-US",
    }

    base = "https://connectapi.garmin.com"

    # Профиль
    r = requests.get(f"{base}/userprofile-service/userprofile/personal-information", headers=headers)
    print(f"Profile status: {r.status_code}, body: {r.text[:300]}")
    profile = r.json()
    display_name = profile.get("displayName") or profile.get("userName", "")
    print(f"✅ display_name: {display_name}")

    steps, calories, resting_hr, stress, sleep_hours, battery = 0, 0, 0, 0, 0, 0

    r2 = requests.get(f"{base}/usersummary-service/usersummary/daily/{display_name}?calendarDate={today_str}", headers=headers)
    print(f"Stats status: {r2.status_code}, body: {r2.text[:200]}")
    if r2.ok and r2.text:
        stats = r2.json()
        calories   = int(stats.get("totalKilocalories", 0))
        resting_hr = stats.get("restingHeartRate", 0)
        stress     = stats.get("averageStressLevel", 0)
        steps      = stats.get("totalSteps", 0)

    r3 = requests.get(f"{base}/wellness-service/wellness/dailySleepData/{display_name}?date={today_str}&nonSleepBufferMinutes=60", headers=headers)
    print(f"Sleep status: {r3.status_code}")
    if r3.ok and r3.text:
        sd = r3.json()
        if sd and "dailySleepDTO" in sd:
            sleep_hours = round(sd["dailySleepDTO"].get("sleepTimeSeconds", 0) / 3600, 1)

    r4 = requests.get(f"{base}/wellness-service/wellness/bodyBattery/reading/day/{today_str}", headers=headers)
    print(f"Battery status: {r4.status_code}")
    if r4.ok and r4.text:
        bb = r4.json()
        if isinstance(bb, list) and bb:
            last = bb[-1]
            battery = last[1] if isinstance(last, list) else last.get("bodyBatteryLevel", 0)

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
