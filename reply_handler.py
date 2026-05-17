import os
from flask import Flask, request
from telegram_bot import send_message
from storage import load_articles, save_articles
from tweet_pipeline import run_generation_pipeline, format_drafts_message
from command_handlers import (
    handle_approval_command,
    handle_regen_command,
    handle_refresh_command,
)


app = Flask(__name__)


def handle_reply(user_reply):
    print(f"Received Telegram reply: {user_reply}")

    if not user_reply:
        print("No reply found")
        return

    if handle_approval_command(user_reply):
        return

    if handle_regen_command(user_reply):
        return

    if handle_refresh_command(user_reply):
        return

    if not user_reply.isdigit():
        print("Invalid reply")
        send_message("Reply with a story number, or APPROVE <number> after drafts are generated.")
        return

    choice = int(user_reply)
    articles = load_articles()

    if choice < 1 or choice > len(articles):
        print("Choice out of range")
        send_message("Selected story number is out of range. Please choose a valid number.")
        return

    selected = articles[choice - 1]
    context = run_generation_pipeline(selected)
    send_message(format_drafts_message(context))
    print("Drafts sent!")


@app.route('/update-articles', methods=['POST'])
def update_articles():
    data = request.json
    print("Received ranked articles update from main.py")

    save_articles(data or [])

    return {"status": "articles updated successfully"}, 200


@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    print("Webhook hit from Telegram")
    print(data)

    if not data or "message" not in data:
        return {"status": "ignored"}, 200

    user_reply = data["message"].get("text", "")

    handle_reply(user_reply)

    return {"status": "success"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
