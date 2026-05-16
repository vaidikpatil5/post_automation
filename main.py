from news_fetcher import fetch_news
from filter import filter_articles
from ranker import rank_articles
from telegram_bot import send_message
from storage import save_articles
import requests


def main():
    articles = fetch_news()
    filtered = filter_articles(articles)
    ranked = rank_articles(filtered)
    save_articles(ranked)

    message = "🔥 Today's Top Stories:\n\n"

    for i, article in enumerate(ranked, 1):
        message += (
            f"{i}. {article['title']}\n"
            f"📝 Summary: {article['summary']}\n"
            f"📊 Score: {article['score']:.2f}\n"
            f"🔗 {article['link']}\n\n"
        )

    message += "Reply with the story number to generate X post drafts."

    send_message(message)

    # Push ranked articles to webhook server
    response = requests.post(
        "https://YOUR-RAILWAY-APP.up.railway.app/update-articles",
        json=ranked
    )

    print("Railway sync response:", response.json())

    print("Top stories sent!")


if __name__ == "__main__":
    main()
