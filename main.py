import os
import time
import json
import requests
from eitaa.client import EitaaClient

CHANNEL = "irimedu"
CHECK_INTERVAL = 10
STATE_FILE = "state.json"

EITAA_SESSION = os.getenv("EITAA_SESSION")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_last_id():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("last_id", 0)
    except Exception:
        return 0


def set_last_id(message_id):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_id": message_id}, f)


def telegram_send(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    r = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        },
        timeout=30
    )

    r.raise_for_status()


def main():

    if not EITAA_SESSION:
        raise Exception("EITAA_SESSION is missing")

    if not TELEGRAM_BOT_TOKEN:
        raise Exception("TELEGRAM_BOT_TOKEN is missing")

    if not TELEGRAM_CHAT_ID:
        raise Exception("TELEGRAM_CHAT_ID is missing")

    print("Eitaa -> Telegram started")
    print("Channel:", CHANNEL)

    client = EitaaClient(session=EITAA_SESSION)

    last_id = get_last_id()

    while True:

        try:
            messages = client.get_messages(CHANNEL)

            messages = sorted(
                messages,
                key=lambda x: int(getattr(x, "id", 0))
            )

            newest_id = last_id

            for msg in messages:

                msg_id = int(getattr(msg, "id", 0))

                if msg_id <= last_id:
                    continue

                text = getattr(msg, "text", None)

                if text and text.strip():

                    telegram_send(text)

                    print(
                        "Forwarded Eitaa message:",
                        msg_id
                    )

                newest_id = max(newest_id, msg_id)

            if newest_id > last_id:
                last_id = newest_id
                set_last_id(last_id)

        except Exception as e:
            print("ERROR:", repr(e))

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
