import os
from telegram_bot import send_message
from google import genai
from flask import Flask, request
from config import get_env
from storage import load_articles, save_articles

BOT_TOKEN = get_env("BOT_TOKEN")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY. Set it in .env.")

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

def handle_reply(user_reply):
    print(f"Received Telegram reply: {user_reply}")

    if not user_reply:
        print("No reply found")
        return

    if not user_reply.isdigit():
        print("Invalid reply")
        return

    choice = int(user_reply)

    articles = load_articles()

    if choice < 1 or choice > len(articles):
        print("Choice out of range")
        return

    selected = articles[choice - 1]

    prompt = f"""
    You are writing content for X (Twitter) focused on startups, product, growth, fintech, and business strategy.

    Writing style rules:
    - concise and sharp
    - slightly analytical
    - no cringe hustle language
    - sound like a young product/business operator
    - include one strong insight/opinion

    Based on this news article:

    Title: {selected['title']}
    Summary: {selected['summary']}

    Generate:
    1. One normal tweet
    2. One contrarian take
    3. One thread hook
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    generated_text = response.text

    final_message = (
        f"📰 {selected['title']}\n\n"
        f"🔗 {selected['link']}\n\n"
        f"Generated X Drafts:\n\n"
        f"{generated_text}"
    )

    send_message(final_message)

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
    app.run(host="0.0.0.0", port=port, debug=True)
