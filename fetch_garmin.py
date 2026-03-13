import json
import os
import base64
import tempfile
from datetime import date
import garth

today = date.today()
today_str = today.isoformat()

try:
    oauth1_data = base64.b64decode(os.environ["GARMIN_OAUTH1"]).decode("utf-8")
    oauth2_data = base64.b64decode(os.environ["GARMIN_OAUTH2"]).decode("utf-8")

    # Сохраняем токены во временную папку и грузим через garth.resume
    tmpdir = tempfile.mkdtemp()
    with open(f"{tmpdir}/oauth1_token.json", "w") as f:
        f.write(oauth1_data)
    with open(f"{tmpdir}/oauth2_token.json", "w") as f:
        f.write(oauth2_data)

    garth.resume(tmpdir)
    garth.client.username  # проверяем что авторизован

    display_name = garth.client.profile["displayName"]
    print(f"✅ Профиль: {display_name}")

    steps_data = garth.client.connectapi(f"/wellness-service/wellness/dailySummaryChart/{display_name}?date={today_str}")
    steps = sum(e.get("steps", 0) for e in steps_data) if isinstance(steps_data, list) else 0

    stats = garth.client.connectapi(f"/usersummary-service/usersummary/daily/{display_name}?calendarDate={today_str}")
    calories   = int(stats.get("totalKilocalories", 0))
    resting_hr = stats.get("restingHeartRate", 0)
    stress     = stats.get("averageStressLevel", 0)

    sleep_data = garth.client.connectapi(f"/wellness-service/wellness/dailySleepData/{display_name}?date={today_str}&nonSleepBufferMinutes=60")
    sleep_hours = 0
    if sleep_data and "dailySleepDTO" in sleep_data:
        sleep_hours = round(sleep_data["dailySleepDTO"].get("sleepTimeSeconds", 0) / 3600, 1)

    bb_data = garth.client.connectapi(f"/wellness-service/wellness/bodyBattery/reading/day/{today_str}")
    battery = 0
    if isinstance(bb_data, list) and bb_data:
        last = bb_data[-1]
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
