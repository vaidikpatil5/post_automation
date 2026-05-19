from editorial_intelligence import (
    FILTER_THEME_THRESHOLD,
    IRRELEVANT_KEYWORDS,
    build_article_text,
    get_theme_matches,
)


def filter_articles(articles):
    filtered_articles = []
    seen_fingerprints = set()

    for article in articles:
        text = build_article_text(article)
        lowered_text = text.lower()
        thematic_match = get_theme_matches(text)
        article_key = article.get("content_fingerprint") or article.get("title", "").lower().strip()

        irrelevant_match = any(
            keyword in lowered_text for keyword in IRRELEVANT_KEYWORDS
        )

        article["theme_matches"] = thematic_match["matched_themes"]
        article["theme_similarity_score"] = thematic_match["theme_similarity_score"]
        article.setdefault("editorial_metadata", {})
        article["editorial_metadata"]["filter"] = {
            "matched_themes": thematic_match["matched_themes"],
            "theme_similarity_score": thematic_match["theme_similarity_score"],
            "irrelevant_match": irrelevant_match,
            "passed_thematic_filter": thematic_match["theme_similarity_score"] >= FILTER_THEME_THRESHOLD,
        }

        if (
            thematic_match["theme_similarity_score"] >= FILTER_THEME_THRESHOLD
            and not irrelevant_match
            and article_key not in seen_fingerprints
        ):
            filtered_articles.append(article)
            seen_fingerprints.add(article_key)

    return filtered_articles
