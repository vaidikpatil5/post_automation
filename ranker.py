from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

USER_INTEREST = """
business strategy
product growth
product launches
fintech
payments
consumer startups
technology disruption
AI products
SaaS
marketplaces
ecommerce
startup funding
consumer internet
"""


def rank_articles(articles):
    if not articles:
        return []

    article_texts = [
        article["title"] + " " + article["summary"]
        for article in articles
    ]

    interest_embedding = model.encode([USER_INTEREST])
    article_embeddings = model.encode(article_texts)

    scores = cosine_similarity(
        interest_embedding,
        article_embeddings
    )[0]

    ranked_articles = []

    for article, score in zip(articles, scores):
        article["score"] = float(score)
        ranked_articles.append(article)

    ranked_articles.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked_articles[:5]