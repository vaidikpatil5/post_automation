from urllib.parse import urlparse

def build_article_text(article):
    """Build standardized flat text representation of an article for NLP scoring."""
    return f"{article.get('title', '')} {article.get('summary', '')}".strip()

def normalize_domain(url):
    """Extract and normalize domain name from URL."""
    if not url:
        return ""
    domain = urlparse(url).netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain
