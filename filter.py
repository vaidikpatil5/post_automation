RELEVANT_KEYWORDS = [
    "ai",
    "startup",
    "saas",
    "fintech",
    "payments",
    "product",
    "growth",
    "consumer",
    "ecommerce",
    "funding",
    "acquisition",
    "launch",
    "tech"
]

IRRELEVANT_KEYWORDS = [
    "celebrity",
    "politics",
    "sports",
    "movie",
    "entertainment"
]


def filter_articles(articles):
    filtered_articles = []
    seen_titles = set()

    for article in articles:
        text = (
            article["title"] + " " + article["summary"]
        ).lower()

        relevant_match = any(
            keyword in text for keyword in RELEVANT_KEYWORDS
        )

        irrelevant_match = any(
            keyword in text for keyword in IRRELEVANT_KEYWORDS
        )

        normalized_title = article["title"].lower().strip()

        if (
            relevant_match
            and not irrelevant_match
            and normalized_title not in seen_titles
        ):
            filtered_articles.append(article)
            seen_titles.add(normalized_title)

    return filtered_articles