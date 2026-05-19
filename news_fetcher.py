import feedparser
import hashlib
import re
from datetime import datetime, timezone
from editorial_intelligence import normalize_domain

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


def parse_published_at(entry):
    published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published_struct:
        return ""

    return datetime(*published_struct[:6], tzinfo=timezone.utc).isoformat()


def build_content_fingerprint(title, link):
    payload = f"{title}|{link}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def fetch_news():
    articles = []

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            summary = entry.get("summary", "")
            cleaned_summary = clean_summary(summary)
            title = entry.get("title", "")
            link = entry.get("link", "")

            articles.append({
                "source": source,
                "source_domain": normalize_domain(link),
                "title": title,
                "link": link,
                "summary": cleaned_summary,
                "raw_summary": summary,
                "published_at": parse_published_at(entry),
                "content_fingerprint": build_content_fingerprint(title, link),
            })

    return articles


if __name__ == "__main__":
    news = fetch_news()

    for article in news[:5]:
        print(article)
