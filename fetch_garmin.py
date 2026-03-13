import json
import os
from datetime import date, timedelta
from garminconnect import Garmin

email = os.environ["GARMIN_EMAIL"]
password = os.environ["GARMIN_PASSWORD"]

today = date.today()
today_str = today.isoformat()

try:
    client = Garmin(email, password)
    client.login()

    steps_data     = client.get_steps_data(today_str)
    sleep_data     = client.get_sleep_data(today_str)
    stats          = client.get_stats(today_str)
    heart_rate     = client.get_heart_rates(today_str)
    body_battery   = client.get_body_battery(today_str)

    # Steps
    steps = 0
    if steps_data:
        for entry in steps_data:
            steps += entry.get("steps", 0)

    # Sleep
    sleep_hours = 0
    if sleep_data and "dailySleepDTO" in sleep_data:
        sleep_seconds = sleep_data["dailySleepDTO"].get("sleepTimeSeconds", 0)
        sleep_hours = round(sleep_seconds / 3600, 1)

    # Calories
    calories = stats.get("totalKilocalories", 0) if stats else 0

    # Resting heart rate
    resting_hr = stats.get("restingHeartRate", 0) if stats else 0

    # Stress
    stress = stats.get("averageStressLevel", 0) if stats else 0

    # Body battery (last value)
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
        "calories": int(calories),
        "resting_hr": resting_hr,
        "stress": stress,
        "body_battery": battery,
    }

    print(f"✅ Данные получены: {result}")

except Exception as e:
    print(f"⚠️ Ошибка: {e}")
    # Сохраняем пустые данные чтобы не сломать дашборд
    result = {
        "date": today_str,
        "steps": 0,
        "sleep_hours": 0,
        "calories": 0,
        "resting_hr": 0,
        "stress": 0,
        "body_battery": 0,
        "error": str(e)
    }

with open("garmin.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ garmin.json сохранён")
