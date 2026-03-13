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

    tmpdir = tempfile.mkdtemp()
    with open(f"{tmpdir}/oauth1_token.json", "w") as f:
        f.write(oauth1_data)
    with open(f"{tmpdir}/oauth2_token.json", "w") as f:
        f.write(oauth2_data)

    garth.resume(tmpdir)

    # Получаем профиль через garth
    profile = garth.connectapi("/userprofile-service/socialProfile")
    print(f"Profile: {profile}")
    display_name = profile.get("displayName", "")
    print(f"✅ display_name: {display_name}")

    steps, calories, resting_hr, stress, sleep_hours, battery = 0, 0, 0, 0, 0, 0

    try:
        stats = garth.connectapi(f"/usersummary-service/usersummary/daily/{display_name}?calendarDate={today_str}")
        print(f"Stats: {stats}")
        calories   = int(stats.get("totalKilocalories", 0))
        resting_hr = stats.get("restingHeartRate", 0)
        stress     = stats.get("averageStressLevel", 0)
        steps      = stats.get("totalSteps", 0)
    except Exception as e:
        print(f"Stats error: {e}")

    try:
        sd = garth.connectapi(f"/wellness-service/wellness/dailySleepData/{display_name}?date={today_str}&nonSleepBufferMinutes=60")
        if sd and "dailySleepDTO" in sd:
            sleep_hours = round(sd["dailySleepDTO"].get("sleepTimeSeconds", 0) / 3600, 1)
    except Exception as e:
        print(f"Sleep error: {e}")

    try:
        bb = garth.connectapi(f"/wellness-service/wellness/bodyBattery/reading/day/{today_str}")
        if isinstance(bb, list) and bb:
            last = bb[-1]
            battery = last[1] if isinstance(last, list) else last.get("bodyBatteryLevel", 0)
    except Exception as e:
        print(f"Battery error: {e}")

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
