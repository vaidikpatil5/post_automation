import json
import os

FILE_NAME = "ranked_articles.json"


def save_articles(articles):
    with open(FILE_NAME, "w") as f:
        json.dump(articles, f)


def load_articles():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
