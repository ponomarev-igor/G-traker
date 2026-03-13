import json
import os
from datetime import date
from pathlib import Path

import garth
from garth.exc import GarthException


TODAY = date.today().isoformat()
TOKEN_DIR = Path(os.environ.get("GARMIN_TOKEN_DIR", ".garth"))


def load_env_text(name):
    value = os.environ.get(name, "").strip()
    return value or None


def ensure_session():
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)

    try:
        garth.resume(TOKEN_DIR)
        garth.connectapi("/userprofile-service/socialProfile")
        print("Resumed existing Garmin session")
        return
    except Exception as exc:
        print(f"Resume failed: {exc}")

    email = load_env_text("GARMIN_EMAIL")
    password = load_env_text("GARMIN_PASSWORD")
    mfa_code = load_env_text("GARMIN_MFA_CODE")

    if not email or not password:
        raise RuntimeError(
            "Garmin session expired and GARMIN_EMAIL / GARMIN_PASSWORD are not configured."
        )

    if mfa_code:
        result1, result2 = garth.login(email, password, return_on_mfa=True)
        if result1 == "needs_mfa":
            garth.resume_login(result2, mfa_code)
        else:
            print("Logged in with Garmin credentials")
    else:
        garth.login(email, password)
        print("Logged in with Garmin credentials")

    garth.save(TOKEN_DIR)
    print(f"Saved refreshed Garmin session to {TOKEN_DIR}")


def safe_connect(path, default=None, **params):
    try:
        return garth.connectapi(path, params=params if params else None)
    except Exception as exc:
        print(f"Request failed for {path}: {exc}")
        return default


def build_result():
    ensure_session()

    profile = garth.connectapi("/userprofile-service/socialProfile")
    username = getattr(garth.client, "username", None) or profile.get("displayName")
    if not username:
        raise RuntimeError("Garmin username is missing from session and profile response.")

    stats = safe_connect(
        f"/usersummary-service/usersummary/daily/{username}",
        {},
        calendarDate=TODAY,
    )
    sleep = safe_connect(
        f"/wellness-service/wellness/dailySleepData/{username}",
        {},
        date=TODAY,
        nonSleepBufferMinutes=60,
    )
    body_battery = safe_connect(
        f"/wellness-service/wellness/bodyBattery/reading/day/{TODAY}",
        [],
    )

    sleep_hours = 0
    if sleep and "dailySleepDTO" in sleep:
        sleep_hours = round(sleep["dailySleepDTO"].get("sleepTimeSeconds", 0) / 3600, 1)

    battery = 0
    if isinstance(body_battery, list) and body_battery:
        last = body_battery[-1]
        battery = last[1] if isinstance(last, list) else last.get("bodyBatteryLevel", 0)

    garth.save(TOKEN_DIR)

    return {
        "date": TODAY,
        "steps": stats.get("totalSteps", 0),
        "sleep_hours": sleep_hours,
        "calories": int(stats.get("totalKilocalories", 0) or 0),
        "resting_hr": stats.get("restingHeartRate", 0),
        "stress": stats.get("averageStressLevel", 0),
        "body_battery": battery,
    }


def main():
    try:
        result = build_result()
        print(f"Fetched Garmin data: {result}")
    except (GarthException, RuntimeError, OSError, ValueError) as exc:
        print(f"Garmin sync failed: {exc}")
        result = {
            "date": TODAY,
            "steps": 0,
            "sleep_hours": 0,
            "calories": 0,
            "resting_hr": 0,
            "stress": 0,
            "body_battery": 0,
            "error": str(exc),
        }

    with open("garmin.json", "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)
    print("Saved garmin.json")


if __name__ == "__main__":
    main()
