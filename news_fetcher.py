import feedparser
import re

RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "YourStory": "https://yourstory.com/feed",
    "Inc42": "https://inc42.com/feed/",
}


def clean_summary(summary):
    # Remove HTML tags
    clean_text = re.sub(r"<.*?>", "", summary)

    # Remove extra spaces/newlines
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # Limit summary length
    return clean_text[:200] + "..." if len(clean_text) > 200 else clean_text


def fetch_news():
    articles = []

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            summary = entry.get("summary", "")
            cleaned_summary = clean_summary(summary)

            articles.append({
                "source": source,
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": cleaned_summary
            })

    return articles


if __name__ == "__main__":
    news = fetch_news()

    for article in news[:5]:
        print(article)