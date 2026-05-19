import feedparser
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

# Default per-source cap (news sites with high volume use the lower cap).
DEFAULT_ENTRY_LIMIT = 8
HIGH_VOLUME_ENTRY_LIMIT = 15

RSS_FEEDS = {
    # Startup / Tech Media
    "TechCrunch": "https://techcrunch.com/feed/",
    "YourStory": "https://yourstory.com/feed",
    "Inc42": "https://inc42.com/feed/",
    "VentureBeat": "https://venturebeat.com/feed/",

    # AI / Infra / Engineering
    "OpenAI": "https://openai.com/news/rss.xml",
    # Official anthropic.com/news/rss.xml returns 404; mirror maintained by Olshansk/rss-feeds.
    "Anthropic": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "Nvidia Blog": "https://blogs.nvidia.com/feed/",
    "Cloudflare Blog": "https://blog.cloudflare.com/rss/",
    "Stripe Blog": "https://stripe.com/blog/feed.rss",
    "Vercel Blog": "https://vercel.com/atom",
    "GitHub Engineering": "https://github.blog/engineering/feed/",

    # Markets / Finance / Strategy
    # a16z.com/feed/ is empty; Substack is the active publishing surface.
    "a16z": "https://a16z.substack.com/feed",
    "Sequoia": "https://www.sequoiacap.com/feed/",
    "YC": "https://www.ycombinator.com/blog/rss/",

    # Developer / weak-signal sources
    "Hacker News": "https://hnrss.org/frontpage",
    "Product Hunt": "https://www.producthunt.com/feed",
}

HIGH_VOLUME_SOURCES = {
    "Hacker News",
    "TechCrunch",
    "Inc42",
    "YourStory",
}

TIER_1_SOURCES = {
    "OpenAI",
    "Anthropic",
    "Google AI Blog",
    "Nvidia Blog",
    "Cloudflare Blog",
    "Stripe Blog",
    "GitHub Engineering",
}

TIER_2_SOURCES = {
    "a16z",
    "Sequoia",
    "YC",
}

FEED_USER_AGENT = "post-automation/1.0 (+https://github.com/)"


def normalize_domain(url):
    if not url:
        return ""
    domain = urlparse(url).netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def clean_summary(summary):
    clean_text = re.sub(r"<.*?>", "", summary or "")
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text[:200] + "..." if len(clean_text) > 200 else clean_text


def extract_entry_summary(entry):
    for key in ("summary", "description", "content"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, dict):
                body = first.get("value") or first.get("summary")
                if isinstance(body, str) and body.strip():
                    return body
            if isinstance(first, str) and first.strip():
                return first
    return ""


def parse_published_at(entry):
    published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published_struct:
        return ""

    return datetime(*published_struct[:6], tzinfo=timezone.utc).isoformat()


def build_content_fingerprint(title, link):
    payload = f"{title}|{link}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def signal_source_tier(source):
    if source in TIER_1_SOURCES:
        return "tier_1"
    if source in TIER_2_SOURCES:
        return "tier_2"
    return "tier_3"


def parse_feed(url):
    return feedparser.parse(url, agent=FEED_USER_AGENT)


def fetch_news():
    articles = []

    for source, url in RSS_FEEDS.items():
        feed = parse_feed(url)
        entry_count = len(feed.entries)
        bozo = bool(getattr(feed, "bozo", False))

        if entry_count == 0:
            exc = getattr(feed, "bozo_exception", None)
            detail = f" ({exc})" if exc else ""
            print(f"[RSS ERROR] No entries for {source}: {url}{detail}")
            continue

        if bozo:
            exc = getattr(feed, "bozo_exception", None)
            detail = f" — {exc}" if exc else ""
            print(f"[RSS WARN] Parse warning for {source} ({entry_count} entries){detail}")

        entry_limit = (
            HIGH_VOLUME_ENTRY_LIMIT
            if source in HIGH_VOLUME_SOURCES
            else DEFAULT_ENTRY_LIMIT
        )

        added = 0
        for entry in feed.entries[:entry_limit]:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue

            summary = extract_entry_summary(entry)
            cleaned_summary = clean_summary(summary)

            articles.append({
                "source": source,
                "source_domain": normalize_domain(link),
                "title": title,
                "link": link,
                "summary": cleaned_summary,
                "raw_summary": summary,
                "published_at": parse_published_at(entry),
                "content_fingerprint": build_content_fingerprint(title, link),
                "signal_source_tier": signal_source_tier(source),
            })
            added += 1

        print(f"[RSS OK] {source}: {added}/{entry_count} entries")

    return articles


if __name__ == "__main__":
    news = fetch_news()
    print(f"\nTotal articles: {len(news)}")

    by_source = {}
    for article in news:
        by_source[article["source"]] = by_source.get(article["source"], 0) + 1
    for source, count in sorted(by_source.items()):
        print(f"  {source}: {count}")

    for article in news[:5]:
        print(article)
