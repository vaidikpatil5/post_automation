import requests
from config import get_env

BOT_TOKEN = get_env("BOT_TOKEN")
CHAT_ID = get_env("CHAT_ID")


def send_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Missing BOT_TOKEN or CHAT_ID. Set them in .env.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(url, data=payload)

    return response.json()
