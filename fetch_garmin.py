import json
import os
from datetime import date
import garth
from garth.http import OAuth1Token, OAuth2Token
from garminconnect import Garmin

today = date.today()
today_str = today.isoformat()

try:
    oauth1 = json.loads(os.environ["GARMIN_OAUTH1"])
    oauth2 = json.loads(os.environ["GARMIN_OAUTH2"])

    garth.configure(domain="garmin.com")
    garth.client.oauth1_token = OAuth1Token(**oauth1)
    garth.client.oauth2_token = OAuth2Token(**oauth2)

    client = Garmin()
    client.garth = garth.client

    steps_data   = client.get_steps_data(today_str)
    sleep_data   = client.get_sleep_data(today_str)
    stats        = client.get_stats(today_str)
    body_battery = client.get_body_battery(today_str)

    steps = 0
    if steps_data:
        for entry in steps_data:
            steps += entry.get("steps", 0)

    sleep_hours = 0
    if sleep_data and "dailySleepDTO" in sleep_data:
        sleep_seconds = sleep_data["dailySleepDTO"].get("sleepTimeSeconds", 0)
        sleep_hours = round(sleep_seconds / 3600, 1)

    calories   = int(stats.get("totalKilocalories", 0)) if stats else 0
    resting_hr = stats.get("restingHeartRate", 0) if stats else 0
    stress     = stats.get("averageStressLevel", 0) if stats else 0

    battery = 0
    if body_battery and len(body_battery) > 0:
        last = body_battery[-1]
        if isinstance(last, list) and len(last) > 1:
            battery = last[1]
        elif isinstance(last, dict):
            battery = last.get("bodyBatteryLevel", 0)

    result = {
        "date": today_str,
        "steps": steps,
        "sleep_hours": sleep_hours,
        "calories": calories,
        "resting_hr": resting_hr,
        "stress": stress,
        "body_battery": battery,
    }
    print(f"✅ Данные получены: {result}")

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
